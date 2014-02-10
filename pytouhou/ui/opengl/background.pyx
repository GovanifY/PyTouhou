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
          GL_ONE_MINUS_SRC_ALPHA, GL_TEXTURE_2D, glGenBuffers, glEnable,
          glDisable, GL_DEPTH_TEST, glDrawElements, GL_TRIANGLES,
          GL_UNSIGNED_SHORT, GL_ELEMENT_ARRAY_BUFFER)

from .sprite cimport get_sprite_rendering_data


cdef class BackgroundRenderer:
    def __dealloc__(self):
        if self.vertex_buffer != NULL:
            free(self.vertex_buffer)
        if self.indices != NULL:
            free(self.indices)


    def __init__(self, use_fixed_pipeline):
        self.use_fixed_pipeline = use_fixed_pipeline

        if not use_fixed_pipeline:
            glGenBuffers(1, &self.vbo)
            glGenBuffers(1, &self.ibo)


    cdef void render_background(self):
        if self.use_fixed_pipeline:
            indices = self.indices
            glVertexPointer(3, GL_FLOAT, sizeof(Vertex), &self.vertex_buffer[0].x)
            glTexCoordPointer(2, GL_FLOAT, sizeof(Vertex), &self.vertex_buffer[0].u)
            glColorPointer(4, GL_UNSIGNED_BYTE, sizeof(Vertex), &self.vertex_buffer[0].r)
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
            indices = NULL

            #TODO: find a way to use offsetof() instead of those ugly hardcoded values.
            glVertexAttribPointer(0, 3, GL_FLOAT, False, sizeof(Vertex), <void*>0)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 2, GL_FLOAT, False, sizeof(Vertex), <void*>12)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(2, 4, GL_UNSIGNED_BYTE, True, sizeof(Vertex), <void*>20)
            glEnableVertexAttribArray(2)

        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glDrawElements(GL_TRIANGLES, self.nb_indices, GL_UNSIGNED_SHORT, indices)
        glDisable(GL_DEPTH_TEST)

        if not self.use_fixed_pipeline:
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)


    cdef void load(self, background, Renderer renderer):
        cdef float ox, oy, oz, ox2, oy2, oz2
        cdef GLsizei nb_vertices = 0, nb_indices = 0

        vertex_buffer = <Vertex*> malloc(65536 * sizeof(Vertex))
        indices = <GLushort*> malloc(65536 * sizeof(GLushort))

        for ox, oy, oz, model_id, model in background.object_instances:
            for ox2, oy2, oz2, width_override, height_override, sprite in model:
                #TODO: view frustum culling
                data = get_sprite_rendering_data(sprite)
                key = data.key

                x1, x2, x3, x4, y1, y2, y3, y4, z1, z2, z3, z4 = data.pos[0], data.pos[1], data.pos[2], data.pos[3], data.pos[4], data.pos[5], data.pos[6], data.pos[7], data.pos[8], data.pos[9], data.pos[10], data.pos[11]
                r, g, b, a = data.color[0], data.color[1], data.color[2], data.color[3]

                # Pack data
                vertex_buffer[nb_vertices] = Vertex(x1 + ox + ox2, y1 + oy + oy2, z1 + oz + oz2, data.left, data.bottom, r, g, b, a)
                vertex_buffer[nb_vertices+1] = Vertex(x2 + ox + ox2, y2 + oy + oy2, z2 + oz + oz2, data.right, data.bottom, r, g, b, a)
                vertex_buffer[nb_vertices+2] = Vertex(x3 + ox + ox2, y3 + oy + oy2, z3 + oz + oz2, data.right, data.top, r, g, b, a)
                vertex_buffer[nb_vertices+3] = Vertex(x4 + ox + ox2, y4 + oy + oy2, z4 + oz + oz2, data.left, data.top, r, g, b, a)

                # Add indices
                indices[nb_indices] = nb_vertices
                indices[nb_indices+1] = nb_vertices + 1
                indices[nb_indices+2] = nb_vertices + 2
                indices[nb_indices+3] = nb_vertices + 2
                indices[nb_indices+4] = nb_vertices + 3
                indices[nb_indices+5] = nb_vertices

                nb_vertices += 4
                nb_indices += 6

        # We only need to keep the rendered vertices and indices in memory,
        # either in RAM or in VRAM, they will never change until we implement
        # background animation.

        self.texture = renderer.textures[key >> 1]
        self.nb_indices = nb_indices

        if self.use_fixed_pipeline:
            self.vertex_buffer = <Vertex*> realloc(vertex_buffer, nb_vertices * sizeof(Vertex))
            self.indices = <GLushort*> realloc(indices, nb_indices * sizeof(GLushort))
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, nb_vertices * sizeof(Vertex), vertex_buffer, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, nb_indices * sizeof(GLushort), indices, GL_STATIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)