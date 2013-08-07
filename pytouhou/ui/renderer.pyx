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
from itertools import chain

from struct import pack

from pytouhou.lib.opengl cimport \
         (glVertexPointer, glTexCoordPointer, glColorPointer,
          glVertexAttribPointer, glEnableVertexAttribArray, glBlendFunc,
          glBindTexture, glDrawElements, glBindBuffer, glBufferData,
          GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW, GL_UNSIGNED_BYTE,
          GL_UNSIGNED_SHORT, GL_INT, GL_FLOAT, GL_SRC_ALPHA,
          GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_TEXTURE_2D, GL_TRIANGLES,
          glGenBuffers)

from .sprite cimport get_sprite_rendering_data
from .texture import TextureManager


MAX_ELEMENTS = 640*4*3


cdef class Renderer:
    def __cinit__(self):
        # Allocate buffers
        self.vertex_buffer = <Vertex*> malloc(MAX_ELEMENTS * sizeof(Vertex))


    def __dealloc__(self):
        free(self.vertex_buffer)


    def __init__(self, resource_loader):
        self.texture_manager = TextureManager(resource_loader)

        if not self.use_fixed_pipeline:
            glGenBuffers(1, &self.vbo)


    cpdef render_elements(self, elements):
        cdef unsigned short nb_vertices = 0, nb_indices, *new_indices

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
                x1, x2, x3, x4, y1, y2, y3, y4, z1, z2, z3, z4 = vertices
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
            glVertexPointer(3, GL_INT, sizeof(Vertex), &self.vertex_buffer[0].x)
            glTexCoordPointer(2, GL_FLOAT, sizeof(Vertex), &self.vertex_buffer[0].u)
            glColorPointer(4, GL_UNSIGNED_BYTE, sizeof(Vertex), &self.vertex_buffer[0].r)
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, nb_vertices * sizeof(Vertex), &self.vertex_buffer[0], GL_DYNAMIC_DRAW)

            #TODO: find a way to use offsetof() instead of those ugly hardcoded values.
            glVertexAttribPointer(0, 3, GL_INT, False, sizeof(Vertex), <void*>0)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 2, GL_FLOAT, False, sizeof(Vertex), <void*>12)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(2, 4, GL_UNSIGNED_BYTE, True, sizeof(Vertex), <void*>20)
            glEnableVertexAttribArray(2)

        for (texture, blendfunc), indices in indices_by_texture.items():

            #TODO: find a more elegent way.
            nb_indices = len(indices)
            new_indices = <unsigned short*> malloc(nb_indices * sizeof(unsigned short))
            for i in xrange(nb_indices):
                new_indices[i] = indices[i]

            glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[blendfunc])
            glBindTexture(GL_TEXTURE_2D, texture)
            glDrawElements(GL_TRIANGLES, nb_indices, GL_UNSIGNED_SHORT, new_indices)
            free(new_indices)

        if not self.use_fixed_pipeline:
            glBindBuffer(GL_ARRAY_BUFFER, 0)
