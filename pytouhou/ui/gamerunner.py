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

from pyglet.gl import (glMatrixMode, glLoadIdentity, glEnable,
                       glHint, glEnableClientState, glViewport,
                       gluPerspective, gluLookAt,
                       GL_MODELVIEW, GL_PROJECTION,
                       GL_TEXTURE_2D, GL_BLEND, GL_FOG,
                       GL_PERSPECTIVE_CORRECTION_HINT, GL_FOG_HINT, GL_NICEST,
                       GL_COLOR_ARRAY, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY)

from .gamerenderer import GameRenderer


class GameRunner(pyglet.window.Window, GameRenderer):
    def __init__(self, resource_loader, game=None, background=None, replay=None):
        GameRenderer.__init__(self, resource_loader, game, background)
        pyglet.window.Window.__init__(self, caption='PyTouhou', resizable=False)
        self.replay_level = None
        if not replay or not replay.levels[game.stage-1]:
            self.keys = pyglet.window.key.KeyStateHandler()
            self.push_handlers(self.keys)
        else:
            self.keys = 0
            self.replay_level = replay.levels[game.stage-1]

        self.fps_display = pyglet.clock.ClockDisplay()


    def start(self, width=384, height=448):
        self.set_size(width, height)

        # Initialize OpenGL
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(30, float(width)/float(height),
                       101010101./2010101., 101010101./10101.)

        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_FOG)
        glHint(GL_FOG_HINT, GL_NICEST)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glEnableClientState(GL_COLOR_ARRAY)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        # Use our own loop to ensure 60 (for now, 120) fps
        pyglet.clock.set_fps_limit(120)
        while not self.has_exit:
            pyglet.clock.tick()
            self.dispatch_events()
            self.update()
            self.on_draw()
            self.flip()


    def on_resize(self, width, height):
        glViewport(0, 0, width, height)


    def _event_text_symbol(self, ev):
        # XXX: Ugly workaround to a pyglet bug on X11
        #TODO: fix that bug in pyglet
        try:
            return pyglet.window.Window._event_text_symbol(self, ev)
        except Exception as exc:
            print('*WARNING* Pyglet error:')
            traceback.print_exc(exc)
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
                if self.keys[pyglet.window.key.W]:
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
                self.game.run_iter(keystate)
            else:
                keystate = 0
                for frame, _keystate, unknown in self.replay_level.keys:
                    if self.game.frame < frame:
                        break
                    else:
                        keystate = _keystate

                self.game.run_iter(keystate)


    def on_draw(self):
        GameRenderer.render(self)

        #TODO
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(192., 224., 835.979370,
                  192, 224., 0., 0., 1., 0.)
        self.fps_display.draw()

