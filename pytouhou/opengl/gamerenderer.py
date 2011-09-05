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

import pygame

import OpenGL
OpenGL.FORWARD_COMPATIBLE_ONLY = True
from OpenGL.GL import *
from OpenGL.GLU import *


from pytouhou.opengl.texture import TextureManager
from pytouhou.opengl.sprite import get_sprite_rendering_data
from pytouhou.opengl.background import get_background_rendering_data


class GameRenderer(object):
    def __init__(self, resource_loader, game=None, background=None):
        self.texture_manager = TextureManager(resource_loader)

        self.game = game
        self.background = background

        self.window = None


    def start(self, width=384, height=448):
        # Initialize pygame
        pygame.init()
        self.window = pygame.display.set_mode((width, height),
                                              pygame.OPENGL | pygame.DOUBLEBUF)

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


    def render_elements(self, elements):
        texture_manager = self.texture_manager
        objects_by_texture = {}
        for element in elements:
            sprite = element._sprite
            if sprite:
                ox, oy = element.x, element.y
                key, (vertices, uvs, colors) = get_sprite_rendering_data(sprite)
                rec = objects_by_texture.setdefault(key, ([], [], []))
                vertices = ((x + ox, y + oy, z) for x, y, z in vertices)
                rec[0].extend(vertices)
                rec[1].extend(uvs)
                rec[2].extend(colors)

        for (texture_key, blendfunc), (vertices, uvs, colors) in objects_by_texture.items():
            nb_vertices = len(vertices)
            glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[blendfunc])
            glBindTexture(GL_TEXTURE_2D, texture_manager[texture_key])
            glVertexPointer(3, GL_FLOAT, 0, struct.pack(str(3 * nb_vertices) + 'f', *chain(*vertices)))
            glTexCoordPointer(2, GL_FLOAT, 0, struct.pack(str(2 * nb_vertices) + 'f', *chain(*uvs)))
            glColorPointer(4, GL_UNSIGNED_BYTE, 0, struct.pack(str(4 * nb_vertices) + 'B', *chain(*colors)))
            glDrawArrays(GL_QUADS, 0, nb_vertices)


    def render(self):
        glClear(GL_DEPTH_BUFFER_BIT)

        back = self.background
        game = self.game
        texture_manager = self.texture_manager

        if back is not None:
            fog_b, fog_g, fog_r, _, fog_start, fog_end = back.fog_interpolator.values
            x, y, z = back.position_interpolator.values
            dx, dy, dz = back.position2_interpolator.values

            glFogi(GL_FOG_MODE, GL_LINEAR)
            glFogf(GL_FOG_START, fog_start)
            glFogf(GL_FOG_END,  fog_end)
            glFogfv(GL_FOG_COLOR, (fog_r / 255., fog_g / 255., fog_b / 255., 1.))

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
                glBindTexture(GL_TEXTURE_2D, texture_manager[texture_key])
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

