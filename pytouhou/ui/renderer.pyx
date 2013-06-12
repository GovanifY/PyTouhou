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

from libc.stdlib cimport malloc, free, realloc
from libc.math cimport tan
from math import radians
from itertools import chain

import ctypes

from struct import pack

from pyglet.gl import (glVertexPointer, glTexCoordPointer, glColorPointer,
                       glVertexAttribPointer, glEnableVertexAttribArray,
                       glBlendFunc, glBindTexture, glDrawElements,
                       glBindBuffer, glBufferData, GL_ARRAY_BUFFER,
                       GL_DYNAMIC_DRAW, GL_STATIC_DRAW, GL_UNSIGNED_BYTE, GL_UNSIGNED_SHORT,
                       GL_INT, GL_FLOAT, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                       GL_ONE, GL_TEXTURE_2D, GL_TRIANGLES,
                       glEnable, glDisable, GL_DEPTH_TEST, glDrawArrays, GL_QUADS)

from .sprite cimport get_sprite_rendering_data
from .texture cimport TextureManager
from pytouhou.utils.matrix cimport Matrix
from pytouhou.utils.vector import Vector, normalize, cross, dot


MAX_ELEMENTS = 640*4*3


cdef class Renderer:
    def __cinit__(self):
        # Allocate buffers
        self.vertex_buffer = <Vertex*> malloc(MAX_ELEMENTS * sizeof(Vertex))
        self.background_vertex_buffer = <VertexFloat*> malloc(65536 * sizeof(Vertex))


    def __dealloc__(self):
        free(self.vertex_buffer)
        free(self.background_vertex_buffer)


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

        if nb_vertices == 0:
            return

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


    cpdef render_background(self):
        if self.use_fixed_pipeline:
            glVertexPointer(3, GL_FLOAT, sizeof(VertexFloat), <long> &self.background_vertex_buffer[0].x)
            glTexCoordPointer(2, GL_FLOAT, sizeof(VertexFloat), <long> &self.background_vertex_buffer[0].u)
            glColorPointer(4, GL_UNSIGNED_BYTE, sizeof(VertexFloat), <long> &self.background_vertex_buffer[0].r)
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self.back_vbo)

            #TODO: find a way to use offsetof() instead of those ugly hardcoded values.
            glVertexAttribPointer(0, 3, GL_FLOAT, False, sizeof(VertexFloat), 0)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 2, GL_FLOAT, False, sizeof(VertexFloat), 12)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(2, 4, GL_UNSIGNED_BYTE, True, sizeof(VertexFloat), 20)
            glEnableVertexAttribArray(2)

        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[self.blendfunc])
        glBindTexture(GL_TEXTURE_2D, self.texture_manager[self.texture_key])
        glDrawArrays(GL_QUADS, 0, self.nb_vertices)
        glDisable(GL_DEPTH_TEST)

        if not self.use_fixed_pipeline:
            glBindBuffer(GL_ARRAY_BUFFER, 0)


    cpdef prerender_background(self, background):
        cdef float ox, oy, oz, ox2, oy2, oz2
        cdef unsigned short nb_vertices = 0
        cdef VertexFloat* vertex_buffer

        vertex_buffer = self.background_vertex_buffer

        for ox, oy, oz, model_id, model in background.object_instances:
            for ox2, oy2, oz2, width_override, height_override, sprite in model:
                #TODO: view frustum culling
                key, (vertices, uvs, colors) = get_sprite_rendering_data(sprite)
                (x1, y1, z1), (x2, y2, z2), (x3, y3, z3), (x4, y4, z4) = vertices
                left, right, bottom, top = uvs
                r, g, b, a = colors

                vertex_buffer[nb_vertices] = VertexFloat(x1 + ox + ox2, y1 + oy + oy2, z1 + oz + oz2, left, bottom, r, g, b, a)
                vertex_buffer[nb_vertices+1] = VertexFloat(x2 + ox + ox2, y2 + oy + oy2, z2 + oz + oz2, right, bottom, r, g, b, a)
                vertex_buffer[nb_vertices+2] = VertexFloat(x3 + ox + ox2, y3 + oy + oy2, z3 + oz + oz2, right, top, r, g, b, a)
                vertex_buffer[nb_vertices+3] = VertexFloat(x4 + ox + ox2, y4 + oy + oy2, z4 + oz + oz2, left, top, r, g, b, a)

                nb_vertices += 4

        self.texture_key, self.blendfunc = key
        self.nb_vertices = nb_vertices
        self.background_vertex_buffer = <VertexFloat*> realloc(vertex_buffer, nb_vertices * sizeof(VertexFloat))

        if not self.use_fixed_pipeline:
            glBindBuffer(GL_ARRAY_BUFFER, self.back_vbo)
            glBufferData(GL_ARRAY_BUFFER, nb_vertices * sizeof(VertexFloat), <long> &self.background_vertex_buffer[0], GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)


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

