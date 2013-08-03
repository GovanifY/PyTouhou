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

from pytouhou.lib.opengl cimport \
         (glMatrixMode, glEnable, glDisable, glViewport, glScissor,
          glLoadMatrixf, glGenBuffers, glDeleteBuffers, GL_MODELVIEW,
          GL_FOG, GL_SCISSOR_TEST, glClear, GL_DEPTH_BUFFER_BIT)

from pytouhou.utils.helpers import get_logger
from pytouhou.utils.maths cimport perspective, setup_camera, ortho_2d
from pytouhou.utils.matrix cimport matrix_to_floats

from .gamerenderer import GameRenderer
from .background import BackgroundRenderer
from .music import MusicPlayer, SFXPlayer, NullPlayer
from .shaders.eosd import GameShader, BackgroundShader


logger = get_logger(__name__)


class GameRunner(GameRenderer):
    def __init__(self, window, resource_loader, replay=None, skip=False):
        self.use_fixed_pipeline = window.use_fixed_pipeline #XXX

        GameRenderer.__init__(self, resource_loader)

        self.window = window
        self.replay_level = None
        self.skip = skip
        self.keystate = 0

        self.width = window.width #XXX
        self.height = window.height #XXX

        if not self.use_fixed_pipeline:
            self.game_shader = GameShader()
            self.background_shader = BackgroundShader()
            self.interface_shader = self.game_shader


    def load_game(self, game=None, background=None, bgms=None, replay=None, save_keystates=None):
        self.game = game
        self.background = background

        self.texture_manager.load(game.resource_loader.instanced_anms.values())

        if background:
            self.background_renderer = BackgroundRenderer(self.use_fixed_pipeline)
            self.background_renderer.prerender(background)

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


    def start(self):
        width = self.game.interface.width if self.game else 640
        height = self.game.interface.height if self.game else 480
        if (width, height) != (self.width, self.height):
            self.window.set_size(width, height)

        self.proj = perspective(30, float(self.game.width) / float(self.game.height),
                                101010101./2010101., 101010101./10101.)
        game_view = setup_camera(0, 0, 1)
        self.game_mvp = game_view * self.proj
        self.interface_mvp = ortho_2d(0., float(self.width), float(self.height), 0.)


    def finish(self):
        #TODO: actually clean after buffers are not needed anymore.
        #if not self.use_fixed_pipeline:
        #    vbo_array = (c_uint * 2)(self.vbo, self.back_vbo)
        #    glDeleteBuffers(2, vbo_array)
        pass


    def update(self):
        if self.background:
            self.background.update(self.game.frame)
        for event in sdl.poll_events():
            type_ = event[0]
            if type_ == sdl.KEYDOWN:
                scancode = event[1]
                if scancode == sdl.SCANCODE_ESCAPE:
                    return False #TODO: implement the pause.
            elif type_ == sdl.QUIT:
                return False
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
        if not self.skip:
            self.render_game()
            self.render_interface()
        return True


    def render_game(self):
        # Switch to game projection
        #TODO: move that to GameRenderer?
        x, y = self.game.interface.game_pos
        glViewport(x, y, self.game.width, self.game.height)
        glClear(GL_DEPTH_BUFFER_BIT)
        glScissor(x, y, self.game.width, self.game.height)
        glEnable(GL_SCISSOR_TEST)

        GameRenderer.render(self)

        glDisable(GL_SCISSOR_TEST)


    def render_interface(self):
        interface = self.game.interface
        interface.labels['framerate'].set_text('%.2ffps' % self.window.clock.get_fps())

        if self.use_fixed_pipeline:
            glMatrixMode(GL_MODELVIEW)
            glLoadMatrixf(matrix_to_floats(self.interface_mvp))
            glDisable(GL_FOG)
        else:
            self.interface_shader.bind()
            self.interface_shader.uniform_matrix('mvp', self.interface_mvp)
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

