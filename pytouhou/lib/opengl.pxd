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


cdef extern from 'epoxy/gl.h' nogil:
    ctypedef unsigned int GLuint
    ctypedef unsigned short GLushort
    ctypedef int GLint
    ctypedef float GLfloat
    ctypedef char GLboolean
    ctypedef char GLchar
    ctypedef unsigned int GLsizei
    ctypedef unsigned int GLsizeiptr
    ctypedef unsigned int GLbitfield
    ctypedef void GLvoid

    ctypedef enum GLenum_blendfunc 'GLenum':
        GL_SRC_ALPHA
        GL_ONE_MINUS_SRC_ALPHA
        GL_ONE
        GL_ZERO

    ctypedef enum GLenum_type 'GLenum':
        GL_UNSIGNED_BYTE
        GL_UNSIGNED_SHORT
        GL_SHORT
        GL_FLOAT
        GL_UNSIGNED_SHORT_5_6_5
        GL_UNSIGNED_SHORT_4_4_4_4
        GL_UNSIGNED_SHORT_4_4_4_4_REV

    ctypedef enum GLenum_format 'GLenum':
        GL_BGRA
        GL_RGBA
        GL_RGB
        GL_LUMINANCE

    ctypedef enum GLenum_bitfield 'GLenum':
        GL_COLOR_BUFFER_BIT
        GL_DEPTH_BUFFER_BIT

    ctypedef GLenum GLenum_textarget

    ctypedef enum GLenum_texparam 'GLenum':
        GL_TEXTURE_MIN_FILTER
        GL_TEXTURE_MAG_FILTER

    ctypedef enum GLenum_store 'GLenum':
        GL_PACK_INVERT_MESA

    ctypedef enum GLenum_client_state 'GLenum':
        GL_COLOR_ARRAY
        GL_VERTEX_ARRAY
        GL_TEXTURE_COORD_ARRAY

    ctypedef enum GLenum_matrix 'GLenum':
        GL_MODELVIEW
        GL_PROJECTION

    ctypedef enum GLenum_fog 'GLenum':
        GL_FOG_MODE
        GL_FOG_START
        GL_FOG_END
        GL_FOG_COLOR

    ctypedef enum GLenum_hint 'GLenum':
        GL_FOG_HINT
        GL_PERSPECTIVE_CORRECTION_HINT

    ctypedef enum GLenum_quality 'GLenum':
        GL_NICEST

    ctypedef enum GLenum_mode 'GLenum':
        GL_QUADS
        GL_TRIANGLES
        GL_TRIANGLE_STRIP

    ctypedef enum GLenum_buffer 'GLenum':
        GL_ARRAY_BUFFER
        GL_ELEMENT_ARRAY_BUFFER

    ctypedef enum GLenum_usage 'GLenum':
        GL_STATIC_DRAW
        GL_DYNAMIC_DRAW

    ctypedef enum GLenum_shader 'GLenum':
        GL_VERTEX_SHADER
        GL_FRAGMENT_SHADER

    ctypedef enum GLenum_shader_param 'GLenum':
        GL_INFO_LOG_LENGTH
        GL_COMPILE_STATUS
        GL_LINK_STATUS

    ctypedef enum GLenum_framebuffer 'GLenum':
        GL_FRAMEBUFFER
        GL_READ_FRAMEBUFFER

    ctypedef enum GLenum_renderbuffer 'GLenum':
        GL_RENDERBUFFER

    ctypedef enum GLenum_renderbuffer_format 'GLenum':
        GL_DEPTH_COMPONENT16

    ctypedef enum GLenum_attachment 'GLenum':
        GL_COLOR_ATTACHMENT0
        GL_DEPTH_ATTACHMENT

    ctypedef enum GLenum_framebuffer_status 'GLenum':
        GL_FRAMEBUFFER_COMPLETE

    ctypedef enum GLenum_debug 'GLenum':
        GL_DEBUG_SOURCE_APPLICATION

    ctypedef enum GLenum:
        GL_BLEND
        GL_TEXTURE_2D
        GL_DEPTH_TEST
        GL_LINEAR
        GL_SCISSOR_TEST
        GL_FOG
        GL_PRIMITIVE_RESTART

    void glVertexPointer(GLint size, GLenum_type type_, GLsizei stride, GLvoid *pointer)
    void glTexCoordPointer(GLint size, GLenum_type type_, GLsizei stride, GLvoid *pointer)
    void glColorPointer(GLint size, GLenum_type type_, GLsizei stride, GLvoid *pointer)

    void glBlendFunc(GLenum_blendfunc sfactor, GLenum_blendfunc dfactor)
    void glDrawArrays(GLenum_mode mode, GLint first, GLsizei count)
    void glDrawElements(GLenum_mode mode, GLsizei count, GLenum_type type_, const GLvoid *indices)
    void glEnable(GLenum cap)
    void glDisable(GLenum cap)

    void glGenTextures(GLsizei n, GLuint *textures)
    void glDeleteTextures(GLsizei n, const GLuint *textures)
    void glBindTexture(GLenum_textarget target, GLuint texture)
    void glTexParameteri(GLenum_textarget target, GLenum_texparam pname, GLint param)
    void glTexImage2D(GLenum_textarget target, GLint level, GLint internalFormat, GLsizei width, GLsizei height, GLint border, GLenum_format format_, GLenum_type type_, const GLvoid *data)
    void glGetTexImage(GLenum_textarget target, GLint level, GLenum_format format_, GLenum_type type_, GLvoid *img)
    void glPixelStorei(GLenum_store pname, GLint param)

    void glClearColor(GLfloat red, GLfloat green, GLfloat blue, GLfloat alpha)
    void glClear(GLbitfield mask)
    void glViewport(GLint x, GLint y, GLsizei width, GLsizei height)
    void glScissor(GLint x, GLint y, GLsizei width, GLsizei height)
    void glMatrixMode(GLenum_matrix mode)
    void glLoadIdentity()
    void glLoadMatrixf(const GLfloat * m)

    void glFogi(GLenum_fog pname, GLint param)
    void glFogf(GLenum_fog pname, GLfloat param)
    void glFogfv(GLenum_fog pname, const GLfloat * params)

    void glHint(GLenum_hint target, GLenum_quality mode)
    void glEnableClientState(GLenum_client_state cap)

    # Here start non-1.x declarations.

    void glVertexAttribPointer(GLuint index, GLint size, GLenum_type type_, GLboolean normalized, GLsizei stride, const GLvoid *pointer)
    void glEnableVertexAttribArray(GLuint index)

    void glGenBuffers(GLsizei n, GLuint * buffers)
    void glDeleteBuffers(GLsizei n, const GLuint * buffers)
    void glBindBuffer(GLenum_buffer target, GLuint buffer_)
    void glBufferData(GLenum_buffer target, GLsizeiptr size, const GLvoid *data, GLenum_usage usage)

    GLuint glCreateProgram()
    GLuint glCreateShader(GLenum_shader shaderType)
    void glLinkProgram(GLuint program)
    void glUseProgram(GLuint program)
    void glGetProgramiv(GLuint program, GLenum_shader_param pname, GLint *params)
    void glGetProgramInfoLog(GLuint program, GLsizei maxLength, GLsizei *length, GLchar *infoLog)

    void glShaderSource(GLuint shader, GLsizei count, const GLchar **string, const GLint *length)
    void glCompileShader(GLuint shader)
    void glGetShaderiv(GLuint shader, GLenum_shader_param pname, GLint *params)
    void glGetShaderInfoLog(GLuint shader, GLsizei maxLength, GLsizei *length, GLchar *infoLog)
    void glAttachShader(GLuint program, GLuint shader)

    GLint glGetUniformLocation(GLuint program, const GLchar *name)
    void glBindAttribLocation(GLuint program, GLuint index, const GLchar *name)
    void glUniform1fv(GLint location, GLsizei count, const GLfloat *value)
    void glUniform4fv(GLint location, GLsizei count, const GLfloat *value)
    void glUniformMatrix4fv(GLint location, GLsizei count, GLboolean transpose, const GLfloat *value)

    void glGenFramebuffers(GLsizei n, GLuint *ids)
    void glDeleteFramebuffers(GLsizei n, GLuint *ids)
    void glBindFramebuffer(GLenum_framebuffer target, GLuint framebuffer)
    void glFramebufferTexture2D(GLenum_framebuffer target, GLenum_attachment attachment, GLenum_textarget textarget, GLuint texture, GLint level)

    void glGenRenderbuffers(GLsizei n, GLuint *renderbuffers)
    void glDeleteRenderbuffers(GLsizei n, GLuint *renderbuffers)
    void glBindRenderbuffer(GLenum_renderbuffer target, GLuint renderbuffer)
    void glRenderbufferStorage(GLenum_renderbuffer target, GLenum_renderbuffer_format internalformat, GLsizei width, GLsizei height)
    void glFramebufferRenderbuffer(GLenum_framebuffer target, GLenum_attachment attachment, GLenum_renderbuffer renderbuffertarget, GLuint renderbuffer)
    GLenum_framebuffer_status glCheckFramebufferStatus(GLenum_framebuffer target)
    void glBlitFramebuffer(GLint srcX0, GLint srcY0, GLint srcX1, GLint srcY1, GLint dstX0, GLint dstY0, GLint dstX1, GLint dstY1, GLbitfield mask, GLenum filter_)

    void glGenVertexArrays(GLsizei n, GLuint *arrays)
    void glDeleteVertexArrays(GLsizei n, const GLuint *arrays)
    void glBindVertexArray(GLuint array)

    void glPrimitiveRestartIndex(GLuint index)

    # Debug

    void glPushDebugGroup(GLenum_debug source, GLuint id_, GLsizei length, const char *message)
    void glPopDebugGroup()

    # Non-OpenGL libepoxy functions.

    int epoxy_gl_version()
    bint epoxy_has_gl_extension(const char *extension)
    bint epoxy_is_desktop_gl()
