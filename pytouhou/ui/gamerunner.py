# -*- encoding: utf-8 -*-
##
## Copyright (C) 2011 Thibaut Girka <thib@sitedethib.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##

from pytouhou.lib import sdl

from pyglet.gl import (glMatrixMode, glLoadIdentity, glEnable, glDisable,
                       glHint, glEnableClientState, glViewport, glScissor,
                       glLoadMatrixf, glGenBuffers, glDeleteBuffers,
                       GL_MODELVIEW, GL_PROJECTION,
                       GL_TEXTURE_2D, GL_BLEND, GL_FOG,
                       GL_PERSPECTIVE_CORRECTION_HINT, GL_FOG_HINT, GL_NICEST,
                       GL_COLOR_ARRAY, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY,
                       GL_SCISSOR_TEST)

from pytouhou.utils.helpers import get_logger
from pytouhou.utils.maths import perspective, setup_camera, ortho_2d

from .gamerenderer import GameRenderer
from .music import MusicPlayer, SFXPlayer, NullPlayer
from .shaders.eosd import GameShader, BackgroundShader

from ctypes import c_uint, byref


logger = get_logger(__name__)


class Clock(object):
    def __init__(self, fps=None):
        self._target_fps = 0
        self._ref_tick = 0
        self._ref_frame = 0
        self._fps_tick = 0
        self._fps_frame = 0
        self._rate = 0
        self.set_target_fps(fps)


    def set_target_fps(self, fps):
        self._target_fps = fps
        self._ref_tick = 0
        self._fps_tick = 0


    def get_fps(self):
        return self._rate


    def tick(self):
        current = sdl.get_ticks()

        if not self._ref_tick:
            self._ref_tick = current
            self._ref_frame = 0

        if self._fps_frame >= (self._target_fps or 60):
            self._rate = self._fps_frame * 1000. / (current - self._fps_tick)
            self._fps_tick = current
            self._fps_frame = 0

        self._ref_frame += 1
        self._fps_frame += 1

        target_tick = self._ref_tick
        if self._target_fps:
            target_tick += int(self._ref_frame * 1000 / self._target_fps)

        if current <= target_tick:
            sdl.delay(target_tick - current)
        else:
            self._ref_tick = current
            self._ref_frame = 0


class GameRunner(GameRenderer):
    def __init__(self, resource_loader, game=None, background=None, replay=None, double_buffer=True, fps_limit=60, fixed_pipeline=False, skip=False):
        GameRenderer.__init__(self, resource_loader, game, background)

        sdl.init(sdl.INIT_VIDEO)
        sdl.img_init(sdl.INIT_PNG)
        sdl.mix_init(0)

        sdl.gl_set_attribute(sdl.GL_CONTEXT_MAJOR_VERSION, 2)
        sdl.gl_set_attribute(sdl.GL_CONTEXT_MINOR_VERSION, 1)
        sdl.gl_set_attribute(sdl.GL_DOUBLEBUFFER, int(double_buffer))
        sdl.gl_set_attribute(sdl.GL_DEPTH_SIZE, 24)

        self.width, self.height = (game.interface.width, game.interface.height) if game else (640, 480)
        self.win = sdl.Window('PyTouhou',
                              sdl.WINDOWPOS_CENTERED, sdl.WINDOWPOS_CENTERED,
                              self.width, self.height,
                              sdl.WINDOW_OPENGL | sdl.WINDOW_SHOWN)
        self.win.gl_create_context()

        sdl.mix_open_audio(44100, sdl.DEFAULT_FORMAT, 2, 4096)
        sdl.mix_allocate_channels(26) #TODO: make it dependent on the SFX number.

        self.fps_limit = fps_limit
        self.use_fixed_pipeline = fixed_pipeline
        self.replay_level = None
        self.skip = skip
        self.has_exit = False
        self.keystate = 0

        if not self.use_fixed_pipeline:
            self.game_shader = GameShader()
            self.background_shader = BackgroundShader()
            self.interface_shader = self.game_shader

            vbo_array = (c_uint * 2)()
            glGenBuffers(2, vbo_array)
            self.vbo, self.back_vbo = vbo_array

        if game:
            self.load_game(game, background, replay)

        self.clock = Clock(self.fps_limit)


    def load_game(self, game=None, background=None, bgms=None, replay=None, save_keystates=None):
        GameRenderer.load_game(self, game, background)
        self.set_input(replay)
        if replay and replay.levels[game.stage - 1]:
            game.players[0].state.lives = self.replay_level.lives
            game.players[0].state.power = self.replay_level.power
            game.players[0].state.bombs = self.replay_level.bombs
            game.difficulty = self.replay_level.difficulty

        self.save_keystates = save_keystates

        game.music = MusicPlayer(game.resource_loader, bgms)
        game.music.play(0)
        game.sfx_player = SFXPlayer(game.resource_loader) if not self.skip else NullPlayer()


    def set_input(self, replay=None):
        if not replay or not replay.levels[self.game.stage-1]:
            self.replay_level = None
        else:
            self.replay_level = replay.levels[self.game.stage-1]
            self.keys = self.replay_level.iter_keystates()


    def set_size(self, width, height):
        self.win.set_window_size(width, height)


    def start(self, width=None, height=None):
        width = width or (self.game.interface.width if self.game else 640)
        height = height or (self.game.interface.height if self.game else 480)
        if (width, height) != (self.width, self.height):
            self.set_size(width, height)

        # Initialize OpenGL
        glEnable(GL_BLEND)
        if self.use_fixed_pipeline:
            glEnable(GL_TEXTURE_2D)
            glHint(GL_FOG_HINT, GL_NICEST)
            glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
            glEnableClientState(GL_COLOR_ARRAY)
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        self.proj = perspective(30, float(self.game.width) / float(self.game.height),
                                101010101./2010101., 101010101./10101.)
        game_view = setup_camera(0, 0, 1)
        self.game_mvp = game_view * self.proj
        self.interface_mvp = ortho_2d(0., float(self.width), float(self.height), 0.)

        while not self.has_exit:
            if not self.skip:
                self.update()
                self.render_game()
                self.render_interface()
                self.win.gl_swap_window()
                self.clock.tick()
            else:
                self.update()

        if not self.use_fixed_pipeline:
            vbo_array = (c_uint * 2)(self.vbo, self.back_vbo)
            glDeleteBuffers(2, vbo_array)

        self.win.gl_delete_context()
        self.win.destroy_window()
        sdl.mix_close_audio()
        sdl.mix_quit()
        sdl.img_quit()
        sdl.quit()


    def update(self):
        if self.background:
            self.background.update(self.game.frame)
        for event in sdl.poll_events():
            type_ = event[0]
            if type_ == sdl.KEYDOWN:
                scancode = event[1]
                if scancode == sdl.SCANCODE_ESCAPE:
                    self.has_exit = True #TODO: implement the pause.
            elif type_ == sdl.QUIT:
                self.has_exit = True
        if self.game:
            if not self.replay_level:
                #TODO: allow user settings
                keys = sdl.get_keyboard_state()
                keystate = 0
                if keys[sdl.SCANCODE_Z]:
                    keystate |= 1
                if keys[sdl.SCANCODE_X]:
                    keystate |= 2
                if keys[sdl.SCANCODE_LSHIFT]:
                    keystate |= 4
                if keys[sdl.SCANCODE_UP]:
                    keystate |= 16
                if keys[sdl.SCANCODE_DOWN]:
                    keystate |= 32
                if keys[sdl.SCANCODE_LEFT]:
                    keystate |= 64
                if keys[sdl.SCANCODE_RIGHT]:
                    keystate |= 128
                if keys[sdl.SCANCODE_LCTRL]:
                    keystate |= 256
            else:
                try:
                    keystate = self.keys.next()
                except StopIteration:
                    keystate = 0
                    if self.skip:
                        self.set_input()
                        self.skip = False
                        self.game.sfx_player = SFXPlayer(self.game.resource_loader)

            if self.save_keystates is not None:
                self.save_keystates.append(keystate)

            self.game.run_iter(keystate)


    def render_game(self):
        # Switch to game projection
        #TODO: move that to GameRenderer?
        x, y = self.game.interface.game_pos
        glViewport(x, y, self.game.width, self.game.height)
        glScissor(x, y, self.game.width, self.game.height)
        glEnable(GL_SCISSOR_TEST)

        GameRenderer.render(self)

        glDisable(GL_SCISSOR_TEST)


    def render_interface(self):
        interface = self.game.interface
        interface.labels['framerate'].set_text('%.2ffps' % self.clock.get_fps())

        if self.use_fixed_pipeline:
            glMatrixMode(GL_MODELVIEW)
            glLoadMatrixf(self.interface_mvp.get_c_data())
            glDisable(GL_FOG)
        else:
            self.interface_shader.bind()
            self.interface_shader.uniform_matrixf('mvp', self.interface_mvp.get_c_data())
        glViewport(0, 0, self.width, self.height)

        items = [item for item in interface.items if item.anmrunner and item.anmrunner.running]
        labels = interface.labels.values()

        if items:
            # Redraw all the interface
            self.render_elements(items)
        else:
            # Redraw only changed labels
            labels = [label for label in labels if label.changed]

        self.render_elements(interface.level_start)

        if self.game.boss:
            self.render_elements(interface.boss_items)

        self.render_elements(labels)
        for label in labels:
            label.changed = False

