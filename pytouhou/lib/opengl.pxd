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


IF USE_GLEW:
    cdef extern from 'GL/glew.h' nogil:
        GLenum glewInit()


cdef extern from 'GL/gl.h' nogil:
    ctypedef unsigned int GLuint
    ctypedef int GLint
    ctypedef float GLfloat
    ctypedef float GLclampf
    ctypedef char GLboolean
    ctypedef char GLchar
    ctypedef unsigned int GLsizei
    ctypedef unsigned int GLsizeiptr
    ctypedef unsigned int GLbitfield
    ctypedef void GLvoid

    ctypedef enum GLenum:
        GL_ARRAY_BUFFER
        GL_STATIC_DRAW
        GL_DYNAMIC_DRAW
        GL_UNSIGNED_BYTE
        GL_UNSIGNED_SHORT
        GL_INT
        GL_FLOAT
        GL_SRC_ALPHA
        GL_ONE_MINUS_SRC_ALPHA
        GL_ONE
        GL_ZERO
        GL_TEXTURE_2D
        GL_TRIANGLES
        GL_DEPTH_TEST
        GL_QUADS

        GL_TEXTURE_MIN_FILTER
        GL_TEXTURE_MAG_FILTER
        GL_LINEAR
        GL_BGRA
        GL_RGBA
        GL_RGB
        GL_LUMINANCE
        GL_UNSIGNED_SHORT_5_6_5
        GL_UNSIGNED_SHORT_4_4_4_4_REV

        GL_COLOR_BUFFER_BIT
        GL_SCISSOR_TEST
        GL_MODELVIEW
        GL_FOG

        GL_DEPTH_BUFFER_BIT
        GL_PROJECTION
        GL_FOG_MODE
        GL_FOG_START
        GL_FOG_END
        GL_FOG_COLOR

        GL_BLEND
        GL_PERSPECTIVE_CORRECTION_HINT
        GL_FOG_HINT
        GL_NICEST
        GL_COLOR_ARRAY
        GL_VERTEX_ARRAY
        GL_TEXTURE_COORD_ARRAY

        GL_VERTEX_SHADER
        GL_FRAGMENT_SHADER
        GL_INFO_LOG_LENGTH
        GL_COMPILE_STATUS
        GL_LINK_STATUS

        GL_FRAMEBUFFER
        GL_COLOR_ATTACHMENT0
        GL_RENDERBUFFER
        GL_DEPTH_COMPONENT
        GL_DEPTH_ATTACHMENT
        GL_FRAMEBUFFER_COMPLETE

    void glVertexPointer(GLint size, GLenum type_, GLsizei stride, GLvoid *pointer)
    void glTexCoordPointer(GLint size, GLenum type_, GLsizei stride, GLvoid *pointer)
    void glColorPointer(GLint size, GLenum type_, GLsizei stride, GLvoid *pointer)
    void glVertexAttribPointer(GLuint index, GLint size, GLenum type_, GLboolean normalized, GLsizei stride, const GLvoid *pointer)
    void glEnableVertexAttribArray(GLuint index)

    void glBlendFunc(GLenum sfactor, GLenum dfactor)
    void glDrawArrays(GLenum mode, GLint first, GLsizei count)
    void glDrawElements(GLenum mode, GLsizei count, GLenum type_, const GLvoid *indices)
    void glEnable(GLenum cap)
    void glDisable(GLenum cap)

    void glGenBuffers(GLsizei n, GLuint * buffers)
    void glDeleteBuffers(GLsizei n, const GLuint * buffers)
    void glBindBuffer(GLenum target, GLuint buffer_)
    void glBufferData(GLenum target, GLsizeiptr size, const GLvoid *data, GLenum usage)

    void glGenTextures(GLsizei n, GLuint *textures)
    void glDeleteTextures(GLsizei n, const GLuint *textures)
    void glBindTexture(GLenum target, GLuint texture)
    void glTexParameteri(GLenum target, GLenum pname, GLint param)
    void glTexImage2D(GLenum target, GLint level, GLint internalFormat, GLsizei width, GLsizei height, GLint border, GLenum format_, GLenum type_, const GLvoid *data)

    void glClearColor(GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) #XXX
    void glClear(GLbitfield mask)
    void glViewport(GLint x, GLint y, GLsizei width, GLsizei height)
    void glScissor(GLint x, GLint y, GLsizei width, GLsizei height)
    void glMatrixMode(GLenum mode)
    void glLoadIdentity()
    void glLoadMatrixf(const GLfloat * m)

    void glFogi(GLenum pname, GLint param)
    void glFogf(GLenum pname, GLfloat param)
    void glFogfv(GLenum pname, const GLfloat * params)

    void glHint(GLenum target, GLenum mode)
    void glEnableClientState(GLenum cap)

    GLuint glCreateProgram()
    GLuint glCreateShader(GLenum shaderType)
    void glLinkProgram(GLuint program)
    void glUseProgram(GLuint program)
    void glGetProgramiv(GLuint program, GLenum pname, GLint *params)
    void glGetProgramInfoLog(GLuint program, GLsizei maxLength, GLsizei *length, GLchar *infoLog)

    void glShaderSource(GLuint shader, GLsizei count, const GLchar **string, const GLint *length)
    void glCompileShader(GLuint shader)
    void glGetShaderiv(GLuint shader, GLenum pname, GLint *params)
    void glGetShaderInfoLog(GLuint shader, GLsizei maxLength, GLsizei *length, GLchar *infoLog)
    void glAttachShader(GLuint program, GLuint shader)

    GLint glGetUniformLocation(GLuint program, const GLchar *name)
    void glBindAttribLocation(GLuint program, GLuint index, const GLchar *name)
    void glUniform1fv(GLint location, GLsizei count, const GLfloat *value)
    void glUniform4fv(GLint location, GLsizei count, const GLfloat *value)
    void glUniformMatrix4fv(GLint location, GLsizei count, GLboolean transpose, const GLfloat *value)

    void glGenFramebuffers(GLsizei n, GLuint *ids)
    void glBindFramebuffer(GLenum target, GLuint framebuffer)
    void glFramebufferTexture2D(GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level)
    void glGenRenderbuffers(GLsizei n, GLuint *renderbuffers)
    void glBindRenderbuffer(GLenum target, GLuint renderbuffer)
    void glRenderbufferStorage(GLenum target, GLenum internalformat, GLsizei width, GLsizei height)
    void glFramebufferRenderbuffer(GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer)
    GLenum glCheckFramebufferStatus(GLenum target)
