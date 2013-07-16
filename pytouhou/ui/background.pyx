# -*- encoding: utf-8 -*-
##
## Copyright (C) 2013 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from pytouhou.lib.opengl cimport \
         (glVertexPointer, glTexCoordPointer, glColorPointer,
          glVertexAttribPointer, glEnableVertexAttribArray, glBlendFunc,
          glBindTexture, glBindBuffer, glBufferData, GL_ARRAY_BUFFER,
          GL_STATIC_DRAW, GL_UNSIGNED_BYTE, GL_FLOAT, GL_SRC_ALPHA,
          GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_TEXTURE_2D, glGenBuffers,
          glEnable, glDisable, GL_DEPTH_TEST, glDrawArrays, GL_QUADS)

from .sprite cimport get_sprite_rendering_data


cdef class BackgroundRenderer:
    def __cinit__(self):
        # Allocate buffers
        self.vertex_buffer = <Vertex*> malloc(65536 * sizeof(Vertex))


    def __dealloc__(self):
        free(self.vertex_buffer)


    def __init__(self, texture_manager, use_fixed_pipeline):
        self.texture_manager = texture_manager
        self.use_fixed_pipeline = use_fixed_pipeline

        if not use_fixed_pipeline:
            glGenBuffers(1, &self.vbo)


    cpdef render_background(self):
        if self.use_fixed_pipeline:
            glVertexPointer(3, GL_FLOAT, sizeof(Vertex), &self.vertex_buffer[0].x)
            glTexCoordPointer(2, GL_FLOAT, sizeof(Vertex), &self.vertex_buffer[0].u)
            glColorPointer(4, GL_UNSIGNED_BYTE, sizeof(Vertex), &self.vertex_buffer[0].r)
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

            #TODO: find a way to use offsetof() instead of those ugly hardcoded values.
            glVertexAttribPointer(0, 3, GL_FLOAT, False, sizeof(Vertex), <void*>0)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 2, GL_FLOAT, False, sizeof(Vertex), <void*>12)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(2, 4, GL_UNSIGNED_BYTE, True, sizeof(Vertex), <void*>20)
            glEnableVertexAttribArray(2)

        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[self.blendfunc])
        glBindTexture(GL_TEXTURE_2D, self.texture_manager[self.texture_key])
        glDrawArrays(GL_QUADS, 0, self.nb_vertices)
        glDisable(GL_DEPTH_TEST)

        if not self.use_fixed_pipeline:
            glBindBuffer(GL_ARRAY_BUFFER, 0)


    cpdef prerender(self, background):
        cdef float ox, oy, oz, ox2, oy2, oz2
        cdef unsigned short nb_vertices = 0
        cdef Vertex* vertex_buffer

        vertex_buffer = self.vertex_buffer

        for ox, oy, oz, model_id, model in background.object_instances:
            for ox2, oy2, oz2, width_override, height_override, sprite in model:
                #TODO: view frustum culling
                key, (vertices, uvs, colors) = get_sprite_rendering_data(sprite)
                (x1, y1, z1), (x2, y2, z2), (x3, y3, z3), (x4, y4, z4) = vertices
                left, right, bottom, top = uvs
                r, g, b, a = colors

                vertex_buffer[nb_vertices] = Vertex(x1 + ox + ox2, y1 + oy + oy2, z1 + oz + oz2, left, bottom, r, g, b, a)
                vertex_buffer[nb_vertices+1] = Vertex(x2 + ox + ox2, y2 + oy + oy2, z2 + oz + oz2, right, bottom, r, g, b, a)
                vertex_buffer[nb_vertices+2] = Vertex(x3 + ox + ox2, y3 + oy + oy2, z3 + oz + oz2, right, top, r, g, b, a)
                vertex_buffer[nb_vertices+3] = Vertex(x4 + ox + ox2, y4 + oy + oy2, z4 + oz + oz2, left, top, r, g, b, a)

                nb_vertices += 4

        self.texture_key, self.blendfunc = key
        self.nb_vertices = nb_vertices
        self.vertex_buffer = <Vertex*> realloc(vertex_buffer, nb_vertices * sizeof(Vertex))

        if not self.use_fixed_pipeline:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, nb_vertices * sizeof(Vertex), &self.vertex_buffer[0], GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
