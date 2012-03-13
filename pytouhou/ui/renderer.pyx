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

from libc.stdlib cimport malloc, free

import ctypes

from struct import pack

from pyglet.gl import *

from .sprite cimport get_sprite_rendering_data
from .texture cimport TextureManager


MAX_ELEMENTS = 640*4*3


cdef class Renderer:
    def __cinit__(self):
        # Allocate buffers
        self.vertex_buffer = <Vertex*> malloc(MAX_ELEMENTS * sizeof(Vertex))


    def __dealloc__(self):
        free(self.vertex_buffer)


    def __init__(self, resource_loader):
        self.texture_manager = TextureManager(resource_loader)


    cpdef render_elements(self, elements):
        cdef unsigned short nb_vertices = 0

        indices_by_texture = {}

        for element in elements:
            if nb_vertices >= MAX_ELEMENTS - 4:
                break

            sprite = element.sprite
            if sprite and sprite.visible:
                ox, oy = element.x, element.y
                key, (vertices, uvs, colors) = get_sprite_rendering_data(sprite)
                rec = indices_by_texture.setdefault(key, [])

                # Pack data in buffer
                (x1, y1, z1), (x2, y2, z2), (x3, y3, z3), (x4, y4, z4) = vertices
                r1, g1, b1, a1, r2, g2, b2, a2, r3, g3, b3, a3, r4, g4, b4, a4 = colors
                u1, v1, u2, v2, u3, v3, u4, v4 = uvs
                self.vertex_buffer[nb_vertices] = Vertex(x1 + ox, y1 + oy, z1, u1, v1, r1, g1, b1, a1)
                self.vertex_buffer[nb_vertices+1] = Vertex(x2 + ox, y2 + oy, z2, u2, v2, r2, g2, b2, a2)
                self.vertex_buffer[nb_vertices+2] = Vertex(x3 + ox, y3 + oy, z3, u3, v3, r3, g3, b3, a3)
                self.vertex_buffer[nb_vertices+3] = Vertex(x4 + ox, y4 + oy, z4, u4, v4, r4, g4, b4, a4)

                # Add indices
                index = nb_vertices
                rec.extend((index, index + 1, index + 2, index + 3))

                nb_vertices += 4

        for (texture_key, blendfunc), indices in indices_by_texture.items():
            glVertexPointer(3, GL_INT, 24, <long> &self.vertex_buffer[0].x)
            glTexCoordPointer(2, GL_FLOAT, 24, <long> &self.vertex_buffer[0].u)
            glColorPointer(4, GL_UNSIGNED_BYTE, 24, <long> &self.vertex_buffer[0].r)

            nb_indices = len(indices)
            indices = pack(str(nb_indices) + 'H', *indices)
            glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[blendfunc])
            glBindTexture(GL_TEXTURE_2D, self.texture_manager[texture_key].id)
            glDrawElements(GL_QUADS, nb_indices, GL_UNSIGNED_SHORT, indices)


    cpdef setup_camera(self, dx, dy, dz):
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            # Some explanations on the magic constants:
            # 192. = 384. / 2. = width / 2.
            # 224. = 448. / 2. = height / 2.
            # 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
            # This is so that objects on the (O, x, y) plane use pixel coordinates
            gluLookAt(192., 224., - 835.979370 * dz,
                      192. + dx, 224. - dy, 0., 0., -1., 0.)

