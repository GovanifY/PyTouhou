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
from libc.string cimport memset

from pytouhou.lib.opengl cimport \
         (glVertexPointer, glTexCoordPointer, glColorPointer,
          glVertexAttribPointer, glEnableVertexAttribArray, glBlendFunc,
          glBindTexture, glDrawElements, glBindBuffer, glBufferData,
          GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW, GL_UNSIGNED_BYTE,
          GL_UNSIGNED_SHORT, GL_INT, GL_FLOAT, GL_SRC_ALPHA,
          GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_TEXTURE_2D, GL_TRIANGLES,
          glGenBuffers)

from pytouhou.game.element cimport Element
from .sprite cimport get_sprite_rendering_data
from .texture import TextureManager


DEF MAX_ELEMENTS = 640*4*3


cdef long find_objects(Renderer self, object elements):
    # Don’t type element as Element, or else the overriding of objects won’t work.
    cdef Element obj
    cdef long i = 0
    for element in elements:
        for obj in element.objects:
            sprite = obj.sprite
            if sprite and sprite.visible:
                # warning: no reference is preserved on the object—assuming the object will not die accidentally
                self.elements[i] = <PyObject*>obj
                i += 1
                if i >= 640*3-4:
                    return i
    return i


cdef class Renderer:
    def __cinit__(self):
        self.vertex_buffer = <Vertex*> malloc(MAX_ELEMENTS * sizeof(Vertex))


    def __dealloc__(self):
        free(self.vertex_buffer)


    def __init__(self, resource_loader):
        self.texture_manager = TextureManager(resource_loader, self)

        if not self.use_fixed_pipeline:
            glGenBuffers(1, &self.vbo)


    def add_texture(self, int texture):
        for i in xrange(2):
            self.indices[i][texture] = <unsigned short*> malloc(65536 * sizeof(unsigned short))


    def remove_texture(self, int texture):
        for i in xrange(2):
            free(self.indices[i][texture])


    cpdef render_elements(self, elements):
        cdef int key
        cdef int x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4, ox, oy
        cdef float left, right, bottom, top
        cdef unsigned char r, g, b, a

        nb_vertices = 0
        memset(self.last_indices, 0, sizeof(self.last_indices))

        nb_elements = find_objects(self, elements)
        for element_idx in xrange(nb_elements):
            element = <object>self.elements[element_idx]
            sprite = element.sprite
            ox, oy = element.x, element.y
            key, (vertices, uvs, colors) = get_sprite_rendering_data(sprite)

            blendfunc = key // MAX_TEXTURES
            texture = key % MAX_TEXTURES

            rec = self.indices[blendfunc][texture]
            next_indice = self.last_indices[key]

            # Pack data in buffer
            x1, x2, x3, x4, y1, y2, y3, y4, z1, z2, z3, z4 = vertices
            left, right, bottom, top = uvs
            r, g, b, a = colors
            self.vertex_buffer[nb_vertices] = Vertex(x1 + ox, y1 + oy, z1, left, bottom, r, g, b, a)
            self.vertex_buffer[nb_vertices+1] = Vertex(x2 + ox, y2 + oy, z2, right, bottom, r, g, b, a)
            self.vertex_buffer[nb_vertices+2] = Vertex(x3 + ox, y3 + oy, z3, right, top, r, g, b, a)
            self.vertex_buffer[nb_vertices+3] = Vertex(x4 + ox, y4 + oy, z4, left, top, r, g, b, a)

            # Add indices
            rec[next_indice] = nb_vertices
            rec[next_indice+1] = nb_vertices + 1
            rec[next_indice+2] = nb_vertices + 2
            rec[next_indice+3] = nb_vertices + 2
            rec[next_indice+4] = nb_vertices + 3
            rec[next_indice+5] = nb_vertices
            self.last_indices[key] += 6

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

        for key in xrange(2 * MAX_TEXTURES):
            nb_indices = self.last_indices[key]
            if not nb_indices:
                continue

            blendfunc = key // MAX_TEXTURES
            texture = key % MAX_TEXTURES

            glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[blendfunc])
            glBindTexture(GL_TEXTURE_2D, texture)
            glDrawElements(GL_TRIANGLES, nb_indices, GL_UNSIGNED_SHORT, self.indices[blendfunc][texture])

        if not self.use_fixed_pipeline:
            glBindBuffer(GL_ARRAY_BUFFER, 0)
