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
from libc.math cimport tan
from math import radians
from itertools import chain

import ctypes

from struct import pack

from pyglet.gl import (glVertexPointer, glTexCoordPointer, glColorPointer,
                       glVertexAttribPointer, glEnableVertexAttribArray,
                       glBlendFunc, glBindTexture, glDrawElements,
                       glBindBuffer, glBufferData, GL_ARRAY_BUFFER,
                       GL_DYNAMIC_DRAW, GL_UNSIGNED_BYTE, GL_UNSIGNED_SHORT,
                       GL_INT, GL_FLOAT, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                       GL_ONE, GL_TEXTURE_2D, GL_TRIANGLES,
                       glEnable, glDisable, GL_DEPTH_TEST, glDrawArrays, GL_QUADS)

from .sprite cimport get_sprite_rendering_data
from .background import get_background_rendering_data
from .texture cimport TextureManager
from pytouhou.utils.matrix cimport Matrix
from pytouhou.utils.vector import Vector, normalize, cross, dot


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

        objects = chain(*[element.objects for element in elements])
        for element in objects:
            if nb_vertices >= MAX_ELEMENTS - 4:
                break

            sprite = element.sprite
            if sprite and sprite.visible:
                ox, oy = element.x, element.y
                key, (vertices, uvs, colors) = get_sprite_rendering_data(sprite)
                rec = indices_by_texture.setdefault(key, [])

                # Pack data in buffer
                (x1, y1, z1), (x2, y2, z2), (x3, y3, z3), (x4, y4, z4) = vertices
                left, right, bottom, top = uvs
                r, g, b, a = colors
                self.vertex_buffer[nb_vertices] = Vertex(x1 + ox, y1 + oy, z1, left, bottom, r, g, b, a)
                self.vertex_buffer[nb_vertices+1] = Vertex(x2 + ox, y2 + oy, z2, right, bottom, r, g, b, a)
                self.vertex_buffer[nb_vertices+2] = Vertex(x3 + ox, y3 + oy, z3, right, top, r, g, b, a)
                self.vertex_buffer[nb_vertices+3] = Vertex(x4 + ox, y4 + oy, z4, left, top, r, g, b, a)

                # Add indices
                index = nb_vertices
                rec.extend((index, index + 1, index + 2, index + 2, index + 3, index))

                nb_vertices += 4

        if self.use_fixed_pipeline:
            glVertexPointer(3, GL_INT, sizeof(Vertex), <long> &self.vertex_buffer[0].x)
            glTexCoordPointer(2, GL_FLOAT, sizeof(Vertex), <long> &self.vertex_buffer[0].u)
            glColorPointer(4, GL_UNSIGNED_BYTE, sizeof(Vertex), <long> &self.vertex_buffer[0].r)
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, nb_vertices * sizeof(Vertex), <long> &self.vertex_buffer[0], GL_DYNAMIC_DRAW)

            #TODO: find a way to use offsetof() instead of those ugly hardcoded values.
            glVertexAttribPointer(0, 3, GL_INT, False, sizeof(Vertex), 0)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 2, GL_FLOAT, False, sizeof(Vertex), 12)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(2, 4, GL_UNSIGNED_BYTE, True, sizeof(Vertex), 20)
            glEnableVertexAttribArray(2)

        for (texture_key, blendfunc), indices in indices_by_texture.items():
            nb_indices = len(indices)
            indices = pack(str(nb_indices) + 'H', *indices)
            glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[blendfunc])
            glBindTexture(GL_TEXTURE_2D, self.texture_manager[texture_key])
            glDrawElements(GL_TRIANGLES, nb_indices, GL_UNSIGNED_SHORT, indices)

        if not self.use_fixed_pipeline:
            glBindBuffer(GL_ARRAY_BUFFER, 0)


    cpdef render_background(self, back):
        glEnable(GL_DEPTH_TEST)
        for (texture_key, blendfunc), (nb_vertices, vertices, uvs, colors) in get_background_rendering_data(back):
            if self.use_fixed_pipeline:
                glVertexPointer(3, GL_FLOAT, 0, vertices)
                glTexCoordPointer(2, GL_FLOAT, 0, uvs)
                glColorPointer(4, GL_UNSIGNED_BYTE, 0, colors)
            else:
                glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, vertices)
                glEnableVertexAttribArray(0)
                glVertexAttribPointer(1, 2, GL_FLOAT, False, 0, uvs)
                glEnableVertexAttribArray(1)
                glVertexAttribPointer(2, 4, GL_UNSIGNED_BYTE, True, 0, colors)
                glEnableVertexAttribArray(2)
            glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[blendfunc])
            glBindTexture(GL_TEXTURE_2D, self.texture_manager[texture_key])
            glDrawArrays(GL_QUADS, 0, nb_vertices)
        glDisable(GL_DEPTH_TEST)


    cpdef ortho_2d(self, left, right, bottom, top):
        mat = Matrix()
        mat[0][0] = 2 / (right - left)
        mat[1][1] = 2 / (top - bottom)
        mat[2][2] = -1
        mat[3][0] = -(right + left) / (right - left)
        mat[3][1] = -(top + bottom) / (top - bottom)
        return mat


    cpdef look_at(self, eye, center, up):
        eye = Vector(eye)
        center = Vector(center)
        up = Vector(up)

        f = normalize(center - eye)
        u = normalize(up)
        s = normalize(cross(f, u))
        u = cross(s, f)

        return Matrix([[s[0], u[0], -f[0], 0],
                       [s[1], u[1], -f[1], 0],
                       [s[2], u[2], -f[2], 0],
                       [-dot(s, eye), -dot(u, eye), dot(f, eye), 1]])


    cpdef perspective(self, fovy, aspect, z_near, z_far):
        top = tan(radians(fovy / 2)) * z_near
        bottom = -top
        left = -top * aspect
        right = top * aspect

        mat = Matrix()
        mat[0][0] = (2 * z_near) / (right - left)
        mat[1][1] = (2 * z_near) / (top - bottom)
        mat[2][2] = -(z_far + z_near) / (z_far - z_near)
        mat[2][3] = -1
        mat[3][2] = -(2 * z_far * z_near) / (z_far - z_near)
        mat[3][3] = 0
        return mat


    cpdef setup_camera(self, dx, dy, dz):
        # Some explanations on the magic constants:
        # 192. = 384. / 2. = width / 2.
        # 224. = 448. / 2. = height / 2.
        # 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
        # This is so that objects on the (O, x, y) plane use pixel coordinates
        return self.look_at((192., 224., - 835.979370 * dz),
                            (192. + dx, 224. - dy, 0.), (0., -1., 0.))

