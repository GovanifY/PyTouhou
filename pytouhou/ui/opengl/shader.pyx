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
    # vert and frag take arrays of source strings the arrays will be
    # concattenated into one string by OpenGL
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
        self.create_shader(vert[0], GL_VERTEX_SHADER)
        # create the fragment shader
        self.create_shader(frag[0], GL_FRAGMENT_SHADER)

        #TODO: put those elsewhere.
        glBindAttribLocation(self.handle, 0, 'in_position')
        glBindAttribLocation(self.handle, 1, 'in_texcoord')
        glBindAttribLocation(self.handle, 2, 'in_color')

        # attempt to link the program
        self.link()

        if use_debug_group:
            glPopDebugGroup()

    cdef void create_shader(self, const GLchar *string, GLenum_shader shader_type):
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

    cdef void link(self):
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

    cdef GLint get_uniform_location(self, name):
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
    cdef void uniform_1(self, name, GLfloat val):
        glUniform1fv(self.get_uniform_location(name), 1, &val)

    # upload a vec4 uniform
    cdef void uniform_4(self, name, GLfloat a, GLfloat b, GLfloat c, GLfloat d):
        cdef GLfloat vals[4]
        vals[0] = a
        vals[1] = b
        vals[2] = c
        vals[3] = d
        glUniform4fv(self.get_uniform_location(name), 1, vals)

    # upload a uniform matrix
    # works with matrices stored as lists,
    # as well as euclid matrices
    cdef void uniform_matrix(self, name, Matrix *mat):
        # obtain the uniform location
        loc = self.get_uniform_location(name)
        # uplaod the 4x4 floating point matrix
        glUniformMatrix4fv(loc, 1, False, <GLfloat*>mat)
