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

import struct
from itertools import chain
import ctypes

import pyglet
from pyglet.gl import *

from pytouhou.opengl.texture import TextureManager
from pytouhou.opengl.sprite import get_sprite_rendering_data
from pytouhou.opengl.background import get_background_rendering_data


MAX_ELEMENTS = 10000


class GameRenderer(pyglet.window.Window):
    def __init__(self, resource_loader, game=None, background=None):
        pyglet.window.Window.__init__(self, caption='PyTouhou', resizable=False)
        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)

        self.texture_manager = TextureManager(resource_loader)

        self.fps_display =         pyglet.clock.ClockDisplay()

        self.game = game
        self.background = background


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

        # Allocate buffers
        buff = ctypes.c_buffer(MAX_ELEMENTS * 4 * (3 * 4 + 2 * 4 + 4))
        self.buffers = (buff,
                        ctypes.byref(buff, 3 * 4),
                        ctypes.byref(buff, 3 * 4 + 2 * 4))

        pyglet.clock.schedule_interval(self.update, 1./120.)
        pyglet.app.run()


    def on_resize(self, width, height):
        glViewport(0, 0, width, height)


    def update(self, dt):
        if self.background:
            self.background.update(self.game.game_state.frame)
        if self.game:
            self.game.run_iter(0) #TODO: self.keys...


    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()
        # XXX: Fullscreen will be enabled the day pyglet stops sucking
        elif symbol == pyglet.window.key.F11:
            self.set_fullscreen(not self.fullscreen)


    def render_elements(self, elements):
        texture_manager = self.texture_manager

        pack_data = struct.Struct('fff ff BBBB' * 4).pack_into
        _vertices, _uvs, _colors = self.buffers

        nb_vertices = 0
        indices_by_texture = {}

        for element in elements:
            sprite = element._sprite
            if sprite:
                ox, oy = element.x, element.y
                key, (vertices, uvs, colors) = get_sprite_rendering_data(sprite)
                rec = indices_by_texture.setdefault(key, [0, []])
                index = rec[0]

                # Pack data in buffer
                (x1, y1, z1), (x2, y2, z2), (x3, y3, z3), (x4, y4, z4) = vertices
                r1, g1, b1, a1, r2, g2, b2, a2, r3, g3, b3, a3, r4, g4, b4, a4 = colors
                u1, v1, u2, v2, u3, v3, u4, v4 = uvs
                pack_data(_vertices, nb_vertices * (3 * 4 + 2 * 4 + 4),
                                            x1 + ox, y1 + oy, z1,
                                            u1, v1,
                                            r1, g1, b1, a1,

                                            x2 + ox, y2 + oy, z2,
                                            u2, v2,
                                            r2, g2, b2, a2,

                                            x3 + ox, y3 + oy, z3,
                                            u3, v3,
                                            r3, g3, b3, a3,

                                            x4 + ox, y4 + oy, z4,
                                            u4, v4,
                                            r4, g4, b4, a4)

                # Add indices
                rec[0] += 4
                rec[1].extend((index, index + 1, index + 2, index + 3))

                nb_vertices += 4

        glVertexPointer(3, GL_FLOAT, 24, _vertices)
        glTexCoordPointer(2, GL_FLOAT, 24, _uvs)
        glColorPointer(4, GL_UNSIGNED_BYTE, 24, _colors)

        for (texture_key, blendfunc), (nb_indices, indices) in indices_by_texture.items():
            indices = struct.pack(str(nb_indices) + 'H', *indices)
            glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[blendfunc])
            glBindTexture(GL_TEXTURE_2D, texture_manager[texture_key].id)
            glDrawElements(GL_QUADS, nb_indices, GL_UNSIGNED_SHORT, indices)


    def on_draw(self):
        glClear(GL_DEPTH_BUFFER_BIT)

        back = self.background
        game = self.game
        texture_manager = self.texture_manager

        if back is not None:
            fog_b, fog_g, fog_r, fog_start, fog_end = back.fog_interpolator.values
            x, y, z = back.position_interpolator.values
            dx, dy, dz = back.position2_interpolator.values

            glFogi(GL_FOG_MODE, GL_LINEAR)
            glFogf(GL_FOG_START, fog_start)
            glFogf(GL_FOG_END,  fog_end)
            glFogfv(GL_FOG_COLOR, (GLfloat * 4)(fog_r / 255., fog_g / 255., fog_b / 255., 1.))

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            # Some explanations on the magic constants:
            # 192. = 384. / 2. = width / 2.
            # 224. = 448. / 2. = height / 2.
            # 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
            # This is so that objects on the (O, x, y) plane use pixel coordinates
            gluLookAt(192., 224., - 835.979370 * dz,
                      192. + dx, 224. - dy, 0., 0., -1., 0.)
            glTranslatef(-x, -y, -z)

            glEnable(GL_DEPTH_TEST)
            for (texture_key, blendfunc), (nb_vertices, vertices, uvs, colors) in get_background_rendering_data(back):
                glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[blendfunc])
                glBindTexture(GL_TEXTURE_2D, texture_manager[texture_key].id)
                glVertexPointer(3, GL_FLOAT, 0, vertices)
                glTexCoordPointer(2, GL_FLOAT, 0, uvs)
                glColorPointer(4, GL_UNSIGNED_BYTE, 0, colors)
                glDrawArrays(GL_QUADS, 0, nb_vertices)
            glDisable(GL_DEPTH_TEST)
        else:
            glClear(GL_COLOR_BUFFER_BIT)

        if game is not None:
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            # Some explanations on the magic constants:
            # 192. = 384. / 2. = width / 2.
            # 224. = 448. / 2. = height / 2.
            # 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
            # This is so that objects on the (O, x, y) plane use pixel coordinates
            gluLookAt(192., 224., - 835.979370,
                      192., 224., 0., 0., -1., 0.)

            glDisable(GL_FOG)
            self.render_elements(game.enemies)
            self.render_elements(game.game_state.bullets)
            glEnable(GL_FOG)

        #TODO
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(192., 224., 835.979370,
                  192, 224., 0., 0., 1., 0.)
        self.fps_display.draw()

