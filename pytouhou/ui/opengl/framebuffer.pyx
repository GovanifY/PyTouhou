# -*- encoding: utf-8 -*-
##
## Copyright (C) 2014 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from libc.stdlib cimport free

from pytouhou.lib.opengl cimport \
         (glPushDebugGroup, glPopDebugGroup, GL_DEBUG_SOURCE_APPLICATION,
          glGenTextures, glDeleteTextures, glBindTexture, glTexParameteri,
          glTexImage2D, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
          GL_TEXTURE_MAG_FILTER, GL_LINEAR, GL_RGBA, GL_UNSIGNED_BYTE,
          glGenRenderbuffers, glDeleteRenderbuffers, glBindRenderbuffer,
          glRenderbufferStorage, GL_RENDERBUFFER, GL_DEPTH_COMPONENT16,
          glGenFramebuffers, glDeleteFramebuffers, glBindFramebuffer,
          glFramebufferTexture2D, glFramebufferRenderbuffer,
          glCheckFramebufferStatus, GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
          GL_DEPTH_ATTACHMENT, GL_FRAMEBUFFER_COMPLETE, glGenBuffers,
          glDeleteBuffers, glBindBuffer, glBufferData, GL_ARRAY_BUFFER,
          GL_STATIC_DRAW, glGenVertexArrays, glDeleteVertexArrays,
          glBindVertexArray, glVertexAttribPointer, GL_SHORT, GL_FLOAT,
          glEnableVertexAttribArray, glDrawArrays, GL_TRIANGLE_STRIP,
          glBlitFramebuffer, GL_READ_FRAMEBUFFER, glClear, GL_COLOR_BUFFER_BIT,
          GL_DEPTH_BUFFER_BIT, glViewport, glBlendFunc, GL_ONE, GL_ZERO)

from pytouhou.utils.maths cimport ortho_2d

from .shaders.eosd import PassthroughShader
from .backend cimport use_debug_group, use_vao, use_framebuffer_blit

cdef class Framebuffer:
    def __init__(self, int x, int y, int width, int height):
        if use_debug_group:
            glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "Framebuffer creation")

        # This texture will receive the game area in native resolution.
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

        # We need a depth buffer, but don’t care about retrieving it.
        glGenRenderbuffers(1, &self.rbo)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT16, width, height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        # The framebuffer is there as a rendering target.
        glGenFramebuffers(1, &self.fbo)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.rbo)
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        if not use_framebuffer_blit:
            # We’ll use only those vertices, everytime.
            self.buf[0] = PassthroughVertex(x, y, 0, 1)
            self.buf[1] = PassthroughVertex(x + width, y, 1, 1)
            self.buf[2] = PassthroughVertex(x, y + height, 0, 0)
            self.buf[3] = PassthroughVertex(x + width, y + height, 1, 0)

            # Now we upload those vertices into a static vbo.
            glGenBuffers(1, &self.vbo)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, sizeof(self.buf), self.buf, GL_STATIC_DRAW)

            # As a performance optimisation, if supported, store the rendering state into a vao.
            if use_vao:
                glGenVertexArrays(1, &self.vao)
                glBindVertexArray(self.vao)
                self.set_state()
                glBindVertexArray(0)

            glBindBuffer(GL_ARRAY_BUFFER, 0)

            # And finally the shader we’ll use to display everything.
            self.shader = PassthroughShader()
            self.mvp = ortho_2d(0., float(width), float(height), 0.)
        else:
            self.x = x
            self.y = y
            self.width = width
            self.height = height

        if use_debug_group:
            glPopDebugGroup()

    def __dealloc__(self):
        if not use_framebuffer_blit:
            glDeleteBuffers(1, &self.vbo)
            if use_vao:
                glDeleteVertexArrays(1, &self.vao)
            if self.mvp != NULL:
                free(self.mvp)
        glDeleteTextures(1, &self.texture)
        glDeleteRenderbuffers(1, &self.rbo)
        glDeleteFramebuffers(1, &self.fbo)

    cpdef bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

    cdef void set_state(self) nogil:
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        #TODO: find a way to use offsetof() instead of those ugly hardcoded values.
        glVertexAttribPointer(0, 2, GL_SHORT, False, sizeof(PassthroughVertex), <void*>0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, False, sizeof(PassthroughVertex), <void*>4)
        glEnableVertexAttribArray(1)

    cdef bint render(self, int x, int y, int width, int height) except True:
        if use_debug_group:
            glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "Framebuffer drawing")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClear(GL_COLOR_BUFFER_BIT)

        if use_framebuffer_blit:
            glBindFramebuffer(GL_READ_FRAMEBUFFER, self.fbo)
            glBlitFramebuffer(self.x, self.y, self.width, self.height,
                              x, y, x + width, y + height,
                              GL_COLOR_BUFFER_BIT, GL_LINEAR)
        else:
            self.shader.bind()
            self.shader.uniform_matrix('mvp', self.mvp)

            glViewport(x, y, width, height)
            glBlendFunc(GL_ONE, GL_ZERO)

            if use_vao:
                glBindVertexArray(self.vao)
            else:
                self.set_state()

            glBindTexture(GL_TEXTURE_2D, self.texture)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            glBindTexture(GL_TEXTURE_2D, 0)

            if use_vao:
                glBindVertexArray(0)
            else:
                glBindBuffer(GL_ARRAY_BUFFER, 0)

        if use_debug_group:
            glPopDebugGroup()
