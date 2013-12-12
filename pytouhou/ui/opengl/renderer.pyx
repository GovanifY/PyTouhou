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
from os.path import join

from pytouhou.lib.opengl cimport \
         (glVertexPointer, glTexCoordPointer, glColorPointer,
          glVertexAttribPointer, glEnableVertexAttribArray, glBlendFunc,
          glBindTexture, glDrawElements, glBindBuffer, glBufferData,
          GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW, GL_UNSIGNED_BYTE,
          GL_UNSIGNED_SHORT, GL_SHORT, GL_FLOAT, GL_SRC_ALPHA,
          GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ZERO, GL_TEXTURE_2D, GL_TRIANGLES,
          glGenBuffers, glBindFramebuffer, glViewport, glDeleteBuffers,
          glGenTextures, glTexParameteri, glTexImage2D, glGenRenderbuffers,
          glBindRenderbuffer, glRenderbufferStorage, glGenFramebuffers,
          glFramebufferTexture2D, glFramebufferRenderbuffer,
          glCheckFramebufferStatus, GL_FRAMEBUFFER, GL_TEXTURE_MIN_FILTER,
          GL_LINEAR, GL_TEXTURE_MAG_FILTER, GL_RGBA, GL_RENDERBUFFER,
          GL_DEPTH_COMPONENT, GL_COLOR_ATTACHMENT0, GL_DEPTH_ATTACHMENT,
          GL_FRAMEBUFFER_COMPLETE, glClear, GL_COLOR_BUFFER_BIT,
          GL_DEPTH_BUFFER_BIT, GLuint, glDeleteTextures,
          GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW, glGenVertexArrays,
          glDeleteVertexArrays, glBindVertexArray)

from pytouhou.lib.sdl import SDLError

from pytouhou.game.element cimport Element
from .sprite cimport get_sprite_rendering_data
from .backend cimport use_vao

from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)


cdef class Texture:
    def __cinit__(self, GLuint texture, Renderer renderer):
        self.texture = texture

        # Find an unused key in the textures array.
        for key in xrange(MAX_TEXTURES):
            if renderer.textures[key] == 0:
                break
        else:
            raise MemoryError('Too many textures currently loaded, consider increasing MAX_TEXTURES (currently %d).' % MAX_TEXTURES)

        self.key = key
        self.pointer = &renderer.textures[key]
        self.pointer[0] = texture
        for i in xrange(2):
            renderer.indices[key][i] = self.indices[i]

        #XXX: keep a reference so that when __dealloc__ is called self.pointer is still valid.
        self.renderer = renderer

    def __dealloc__(self):
        if self.texture:
            glDeleteTextures(1, &self.texture)
        if self.pointer != NULL:
            self.pointer[0] = 0
        # The dangling pointers in renderer.indices doesn’t matter, since we
        # won’t use them if no texture is loaded in that slot.


cdef long find_objects(Renderer self, object elements) except -1:
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
    def __dealloc__(self):
        if not self.use_fixed_pipeline:
            glDeleteBuffers(1, &self.framebuffer_vbo)
            glDeleteBuffers(1, &self.vbo)

            if use_vao:
                glDeleteVertexArrays(1, &self.vao)
                glDeleteVertexArrays(1, &self.framebuffer_vao)


    def __init__(self, resource_loader):
        # Only used in modern GL.
        cdef unsigned short framebuffer_indices[6]

        self.texture_manager = TextureManager(resource_loader, self, Texture)
        font_name = join(resource_loader.game_dir, 'font.ttf')
        try:
            self.font_manager = FontManager(font_name, 16, self, Texture)
        except SDLError:
            self.font_manager = None
            logger.error('Font file “%s” not found, disabling text rendering altogether.', font_name)

        if not self.use_fixed_pipeline:
            framebuffer_indices[:] = [0, 1, 2, 2, 3, 0]

            glGenBuffers(1, &self.vbo)
            glGenBuffers(1, &self.framebuffer_vbo)
            glGenBuffers(1, &self.framebuffer_ibo)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.framebuffer_ibo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(framebuffer_indices), framebuffer_indices, GL_STATIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

            if use_vao:
                glGenVertexArrays(1, &self.vao)
                glBindVertexArray(self.vao)
                self.set_state()

                glGenVertexArrays(1, &self.framebuffer_vao)
                glBindVertexArray(self.framebuffer_vao)
                self.set_framebuffer_state()
                glBindVertexArray(0)


    cdef void set_state(self) nogil:
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        #TODO: find a way to use offsetof() instead of those ugly substractions.
        glVertexAttribPointer(0, 3, GL_SHORT, False, sizeof(Vertex), <void*>0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, False, sizeof(Vertex), <void*>8)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 4, GL_UNSIGNED_BYTE, True, sizeof(Vertex), <void*>16)
        glEnableVertexAttribArray(2)

        glBindBuffer(GL_ARRAY_BUFFER, 0)


    cdef void set_framebuffer_state(self) nogil:
        glBindBuffer(GL_ARRAY_BUFFER, self.framebuffer_vbo)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.framebuffer_ibo)

        #TODO: find a way to use offsetof() instead of those ugly hardcoded values.
        glVertexAttribPointer(0, 2, GL_SHORT, False, sizeof(PassthroughVertex), <void*>0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, False, sizeof(PassthroughVertex), <void*>4)
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)


    cdef void render_elements(self, elements):
        cdef Element element

        nb_elements = find_objects(self, elements)
        if not nb_elements:
            return

        nb_vertices = 0
        memset(self.last_indices, 0, sizeof(self.last_indices))

        for element_idx in xrange(nb_elements):
            element = <object>self.elements[element_idx]
            ox, oy = <short>element.x, <short>element.y
            data = get_sprite_rendering_data(element.sprite)
            key = data.key

            blendfunc = key & 1
            texture = key >> 1

            rec = self.indices[texture][blendfunc]
            next_indice = self.last_indices[key]

            # Pack data in buffer
            x1, x2, x3, x4, y1, y2, y3, y4, z1, z2, z3, z4 = <short>data.pos[0], <short>data.pos[1], <short>data.pos[2], <short>data.pos[3], <short>data.pos[4], <short>data.pos[5], <short>data.pos[6], <short>data.pos[7], <short>data.pos[8], <short>data.pos[9], <short>data.pos[10], <short>data.pos[11]
            r, g, b, a = data.color[0], data.color[1], data.color[2], data.color[3]
            self.vertex_buffer[nb_vertices] = Vertex(x1 + ox, y1 + oy, z1, 0, data.left, data.bottom, r, g, b, a)
            self.vertex_buffer[nb_vertices+1] = Vertex(x2 + ox, y2 + oy, z2, 0, data.right, data.bottom, r, g, b, a)
            self.vertex_buffer[nb_vertices+2] = Vertex(x3 + ox, y3 + oy, z3, 0, data.right, data.top, r, g, b, a)
            self.vertex_buffer[nb_vertices+3] = Vertex(x4 + ox, y4 + oy, z4, 0, data.left, data.top, r, g, b, a)

            # Add indices
            rec[next_indice] = nb_vertices
            rec[next_indice+1] = nb_vertices + 1
            rec[next_indice+2] = nb_vertices + 2
            rec[next_indice+3] = nb_vertices + 2
            rec[next_indice+4] = nb_vertices + 3
            rec[next_indice+5] = nb_vertices
            self.last_indices[key] += 6

            nb_vertices += 4

        if self.use_fixed_pipeline:
            glVertexPointer(3, GL_SHORT, sizeof(Vertex), &self.vertex_buffer[0].x)
            glTexCoordPointer(2, GL_FLOAT, sizeof(Vertex), &self.vertex_buffer[0].u)
            glColorPointer(4, GL_UNSIGNED_BYTE, sizeof(Vertex), &self.vertex_buffer[0].r)
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, nb_vertices * sizeof(Vertex), &self.vertex_buffer[0], GL_DYNAMIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

            if use_vao:
                glBindVertexArray(self.vao)
            else:
                self.set_state()

        # Don’t change the state when it’s not needed.
        previous_blendfunc = -1
        previous_texture = -1

        for key in xrange(2 * MAX_TEXTURES):
            nb_indices = self.last_indices[key]
            if not nb_indices:
                continue

            blendfunc = key & 1
            texture = key >> 1

            if blendfunc != previous_blendfunc:
                glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[blendfunc])
            if texture != previous_texture:
                glBindTexture(GL_TEXTURE_2D, self.textures[texture])
            glDrawElements(GL_TRIANGLES, nb_indices, GL_UNSIGNED_SHORT, self.indices[texture][blendfunc])

            previous_blendfunc = blendfunc
            previous_texture = texture

        glBindTexture(GL_TEXTURE_2D, 0)

        if not self.use_fixed_pipeline and use_vao:
            glBindVertexArray(0)


    cdef void render_quads(self, rects, colors, GLuint texture):
        # There is nothing that batch more than two quads on the same texture, currently.
        cdef Vertex buf[8]
        cdef unsigned short indices[12]
        indices[:] = [0, 1, 2, 2, 3, 0, 4, 5, 6, 6, 7, 4]

        length = len(rects)
        assert length == len(colors)

        for i, r in enumerate(rects):
            c1, c2, c3, c4 = colors[i]

            buf[4*i] = Vertex(r.x, r.y, 0, 0, 0, 0, c1.r, c1.g, c1.b, c1.a)
            buf[4*i+1] = Vertex(r.x + r.w, r.y, 0, 0, 1, 0, c2.r, c2.g, c2.b, c2.a)
            buf[4*i+2] = Vertex(r.x + r.w, r.y + r.h, 0, 0, 1, 1, c3.r, c3.g, c3.b, c3.a)
            buf[4*i+3] = Vertex(r.x, r.y + r.h, 0, 0, 0, 1, c4.r, c4.g, c4.b, c4.a)

        if self.use_fixed_pipeline:
            glVertexPointer(3, GL_SHORT, sizeof(Vertex), &buf[0].x)
            glTexCoordPointer(2, GL_FLOAT, sizeof(Vertex), &buf[0].u)
            glColorPointer(4, GL_UNSIGNED_BYTE, sizeof(Vertex), &buf[0].r)
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, 4 * length * sizeof(Vertex), buf, GL_DYNAMIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

            if use_vao:
                glBindVertexArray(self.vao)
            else:
                self.set_state()

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, texture)
        glDrawElements(GL_TRIANGLES, 6 * length, GL_UNSIGNED_SHORT, indices)


    cdef void render_framebuffer(self, Framebuffer fb):
        cdef PassthroughVertex[4] buf

        assert not self.use_fixed_pipeline

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(self.x, self.y, self.width, self.height)
        glBlendFunc(GL_ONE, GL_ZERO)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if use_vao:
            glBindVertexArray(self.framebuffer_vao)
        else:
            self.set_framebuffer_state()

        buf[0] = PassthroughVertex(fb.x, fb.y, 0, 1)
        buf[1] = PassthroughVertex(fb.x + fb.width, fb.y, 1, 1)
        buf[2] = PassthroughVertex(fb.x + fb.width, fb.y + fb.height, 1, 0)
        buf[3] = PassthroughVertex(fb.x, fb.y + fb.height, 0, 0)

        glBindBuffer(GL_ARRAY_BUFFER, self.framebuffer_vbo)
        glBufferData(GL_ARRAY_BUFFER, sizeof(buf), buf, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glBindTexture(GL_TEXTURE_2D, fb.texture)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_SHORT, NULL)
        glBindTexture(GL_TEXTURE_2D, 0)

        if use_vao:
            glBindVertexArray(0)
        else:
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)


cdef class Framebuffer:
    def __init__(self, int x, int y, int width, int height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        glGenTextures(1, &self.texture)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0,
                     GL_RGBA,
                     width, height,
                     0,
                     GL_RGBA, GL_UNSIGNED_BYTE,
                     NULL)
        glBindTexture(GL_TEXTURE_2D, 0)

        glGenRenderbuffers(1, &self.rbo)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, width, height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        glGenFramebuffers(1, &self.fbo)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.rbo)
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    cpdef bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
