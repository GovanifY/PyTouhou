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

import pyglet
import traceback

from pyglet.gl import (glMatrixMode, glLoadIdentity, glEnable, glDisable,
                       glHint, glEnableClientState, glViewport, glScissor,
                       glLoadMatrixf, glGenBuffers, glDeleteBuffers,
                       GL_MODELVIEW, GL_PROJECTION,
                       GL_TEXTURE_2D, GL_BLEND, GL_FOG,
                       GL_PERSPECTIVE_CORRECTION_HINT, GL_FOG_HINT, GL_NICEST,
                       GL_COLOR_ARRAY, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY,
                       GL_SCISSOR_TEST)

from pytouhou.utils.helpers import get_logger
from pytouhou.utils.matrix import Matrix

from .gamerenderer import GameRenderer
from .music import MusicPlayer, SFXPlayer, NullPlayer
from .shaders.eosd import GameShader, BackgroundShader

from ctypes import c_uint, byref


logger = get_logger(__name__)


class GameRunner(pyglet.window.Window, GameRenderer):
    def __init__(self, resource_loader, game=None, background=None, replay=None, double_buffer=True, fps_limit=60, fixed_pipeline=False, skip=False):
        GameRenderer.__init__(self, resource_loader, game, background)

        config = pyglet.gl.Config(double_buffer=double_buffer)
        width, height = (game.interface.width, game.interface.height) if game else (None, None)
        pyglet.window.Window.__init__(self, width=width, height=height,
                                      caption='PyTouhou', resizable=False,
                                      config=config)

        self.fps_limit = fps_limit
        self.use_fixed_pipeline = fixed_pipeline
        self.replay_level = None
        self.skip = skip

        if not self.use_fixed_pipeline:
            self.game_shader = GameShader()
            self.background_shader = BackgroundShader()
            self.interface_shader = self.game_shader

            vbo_array = (c_uint * 2)()
            glGenBuffers(2, vbo_array)
            self.vbo, self.back_vbo = vbo_array

        if game:
            self.load_game(game, background, replay)

        self.clock = pyglet.clock.get_default()


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
            self.keys = pyglet.window.key.KeyStateHandler()
            self.push_handlers(self.keys)
            self.replay_level = None
        else:
            self.replay_level = replay.levels[self.game.stage-1]
            self.keys = self.replay_level.iter_keystates()


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

        self.proj = self.perspective(30, float(self.game.width) / float(self.game.height),
                                     101010101./2010101., 101010101./10101.)
        game_view = self.setup_camera(0, 0, 1)
        self.game_mvp = game_view * self.proj
        self.interface_mvp = self.ortho_2d(0., float(self.width), float(self.height), 0.)

        if self.fps_limit > 0:
            pyglet.clock.set_fps_limit(self.fps_limit)
        while not self.has_exit:
            if not self.skip:
                pyglet.clock.tick()
                self.dispatch_events()
                self.update()
                self.render_game()
                self.render_interface()
                self.flip()
            else:
                self.update()

        if not self.use_fixed_pipeline:
            vbo_array = (c_uint * 2)(self.vbo, self.back_vbo)
            glDeleteBuffers(2, vbo_array)


    def _event_text_symbol(self, ev):
        # XXX: Ugly workaround to a pyglet bug on X11
        #TODO: fix that bug in pyglet
        try:
            return pyglet.window.Window._event_text_symbol(self, ev)
        except Exception as exc:
            logger.warn('Pyglet error: %s', traceback.format_exc(exc))
            return None, None


    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.has_exit = True
        # XXX: Fullscreen will be enabled the day pyglet stops sucking
        elif symbol == pyglet.window.key.F11:
            self.set_fullscreen(not self.fullscreen)


    def update(self):
        if self.background:
            self.background.update(self.game.frame)
        if self.game:
            if not self.replay_level:
                #TODO: allow user settings
                keystate = 0
                if self.keys[pyglet.window.key.W] or self.keys[pyglet.window.key.Z]:
                    keystate |= 1
                if self.keys[pyglet.window.key.X]:
                    keystate |= 2
                #TODO: on some configurations, LSHIFT is Shift_L when pressed
                # and ISO_Prev_Group when released, confusing the hell out of pyglet
                # and leading to a always-on LSHIFT...
                if self.keys[pyglet.window.key.LSHIFT]:
                    keystate |= 4
                if self.keys[pyglet.window.key.UP]:
                    keystate |= 16
                if self.keys[pyglet.window.key.DOWN]:
                    keystate |= 32
                if self.keys[pyglet.window.key.LEFT]:
                    keystate |= 64
                if self.keys[pyglet.window.key.RIGHT]:
                    keystate |= 128
                if self.keys[pyglet.window.key.LCTRL]:
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

