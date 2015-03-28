# -*- encoding: utf-8 -*-
#
# Copyright Tristam Macdonald 2008.
# Copyright Emmanuel Gil Peyrot 2012.
#
# Distributed under the Boost Software License, Version 1.0
# (see http://www.boost.org/LICENSE_1_0.txt)
#
# Source: https://swiftcoder.wordpress.com/2008/12/19/simple-glsl-wrapper-for-pyglet/
#

from pytouhou.lib.opengl cimport \
         (glCreateProgram, glCreateShader, GL_VERTEX_SHADER,
          GL_FRAGMENT_SHADER, glShaderSource, glCompileShader, glGetShaderiv,
          GL_COMPILE_STATUS, GL_INFO_LOG_LENGTH, glGetShaderInfoLog,
          glAttachShader, glLinkProgram, glGetProgramiv, glGetProgramInfoLog,
          GL_LINK_STATUS, glUseProgram, glGetUniformLocation, glUniform1fv,
          glUniform4fv, glUniformMatrix4fv, glBindAttribLocation,
          glPushDebugGroup, GL_DEBUG_SOURCE_APPLICATION, glPopDebugGroup)

from libc.stdlib cimport malloc, free
from .backend cimport shader_header, use_debug_group


class GLSLException(Exception):
    pass


cdef class Shader:
    def __init__(self, vert=None, frag=None):
        if use_debug_group:
            glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "Program creation")

        # create the program handle
        self.handle = glCreateProgram()
        # we are not linked yet
        self.linked = False

        # cache the uniforms location
        self.location_cache = {}

        # create the vertex shader
        vert_src = vert.encode()
        self.create_shader(vert_src, GL_VERTEX_SHADER)

        # create the fragment shader
        frag_src = frag.encode()
        self.create_shader(frag_src, GL_FRAGMENT_SHADER)

        #TODO: put those elsewhere.
        glBindAttribLocation(self.handle, 0, 'in_position')
        glBindAttribLocation(self.handle, 1, 'in_texcoord')
        glBindAttribLocation(self.handle, 2, 'in_color')

        # attempt to link the program
        self.link()

        if use_debug_group:
            glPopDebugGroup()

    cdef bint create_shader(self, const GLchar *string, GLenum_shader shader_type) except True:
        cdef GLint temp
        cdef const GLchar *strings[2]
        strings[:] = [shader_header, string]

        # create the shader handle
        shader = glCreateShader(shader_type)

        # upload the source strings
        glShaderSource(shader, 2, strings, NULL)

        # compile the shader
        glCompileShader(shader)

        # retrieve the compile status
        glGetShaderiv(shader, GL_COMPILE_STATUS, &temp)

        # if compilation failed, print the log
        if not temp:
            # retrieve the log length
            glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &temp)
            # create a buffer for the log
            temp_buf = <GLchar*>malloc(temp * sizeof(GLchar))
            # retrieve the log text
            glGetShaderInfoLog(shader, temp, NULL, temp_buf)
            buf = temp_buf[:temp]
            free(temp_buf)
            # print the log to the console
            raise GLSLException(buf)
        else:
            # all is well, so attach the shader to the program
            glAttachShader(self.handle, shader)

    cdef bint link(self) except True:
        cdef GLint temp

        # link the program
        glLinkProgram(self.handle)

        # retrieve the link status
        glGetProgramiv(self.handle, GL_LINK_STATUS, &temp)

        # if linking failed, print the log
        if not temp:
            #   retrieve the log length
            glGetProgramiv(self.handle, GL_INFO_LOG_LENGTH, &temp)
            # create a buffer for the log
            temp_buf = <GLchar*>malloc(temp * sizeof(GLchar))
            # retrieve the log text
            glGetProgramInfoLog(self.handle, temp, NULL, temp_buf)
            buf = temp_buf[:temp]
            free(temp_buf)
            # print the log to the console
            raise GLSLException(buf)
        else:
            # all is well, so we are linked
            self.linked = True

    cdef GLint get_uniform_location(self, name) except -1:
        if isinstance(name, str):
            name = name.encode()
        if name not in self.location_cache:
            loc = glGetUniformLocation(self.handle, name)
            if loc == -1:
                raise GLSLException('Undefined {} uniform.'.format(name))
            self.location_cache[name] = loc
        return self.location_cache[name]

    cdef void bind(self) nogil:
        # bind the program
        glUseProgram(self.handle)

    # upload a floating point uniform
    # this program must be currently bound
    cdef bint uniform_1(self, name, GLfloat val) except True:
        glUniform1fv(self.get_uniform_location(name), 1, &val)

    # upload a vec4 uniform
    cdef bint uniform_4(self, name, GLfloat a, GLfloat b, GLfloat c, GLfloat d) except True:
        cdef GLfloat vals[4]
        vals[0] = a
        vals[1] = b
        vals[2] = c
        vals[3] = d
        glUniform4fv(self.get_uniform_location(name), 1, vals)

    # upload a uniform matrix
    # works with matrices stored as lists,
    # as well as euclid matrices
    cdef bint uniform_matrix(self, name, Matrix *mat) except True:
        # obtain the uniform location
        loc = self.get_uniform_location(name)
        # uplaod the 4x4 floating point matrix
        glUniformMatrix4fv(loc, 1, False, <GLfloat*>mat)
