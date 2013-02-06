#
# Copyright Tristam Macdonald 2008.
# Copyright Emmanuel Gil Peyrot 2012.
#
# Distributed under the Boost Software License, Version 1.0
# (see http://www.boost.org/LICENSE_1_0.txt)
#
# Source: https://swiftcoder.wordpress.com/2008/12/19/simple-glsl-wrapper-for-pyglet/
#

from pyglet.gl import (glCreateProgram, glCreateShader, GL_VERTEX_SHADER,
                       GL_FRAGMENT_SHADER, glShaderSource, glCompileShader,
                       glGetShaderiv, GL_COMPILE_STATUS, GL_INFO_LOG_LENGTH,
                       glGetShaderInfoLog, glAttachShader, glLinkProgram,
                       glGetProgramiv, glGetProgramInfoLog, GL_LINK_STATUS,
                       glUseProgram, glGetUniformLocation, glUniform1f,
                       glUniform2f, glUniform3f, glUniform4f, glUniform1i,
                       glUniform2i, glUniform3i, glUniform4i,
                       glUniformMatrix4fv, glBindAttribLocation)

from ctypes import (c_char, c_char_p, c_int, POINTER, byref, cast,
                    create_string_buffer)


class GLSLException(Exception):
    pass


class Shader(object):
    # vert and frag take arrays of source strings the arrays will be
    # concattenated into one string by OpenGL
    def __init__(self, vert=None, frag=None):
        # create the program handle
        self.handle = glCreateProgram()
        # we are not linked yet
        self.linked = False

        # cache the uniforms location
        self.location_cache = {}

        # create the vertex shader
        self.createShader(vert, GL_VERTEX_SHADER)
        # create the fragment shader
        self.createShader(frag, GL_FRAGMENT_SHADER)

        #TODO: put those elsewhere.
        glBindAttribLocation(self.handle, 0, 'in_position')
        glBindAttribLocation(self.handle, 1, 'in_texcoord')
        glBindAttribLocation(self.handle, 2, 'in_color')

        # attempt to link the program
        self.link()

    def load_source(self, path):
        with open(path, 'rb') as file:
            source = file.read()
        return source

    def createShader(self, strings, type):
        count = len(strings)
        # if we have no source code, ignore this shader
        if count < 1:
            return

        # create the shader handle
        shader = glCreateShader(type)

        # convert the source strings into a ctypes pointer-to-char array, and upload them
        # this is deep, dark, dangerous black magick - don't try stuff like this at home!
        src = (c_char_p * count)(*strings)
        glShaderSource(shader, count, cast(byref(src), POINTER(POINTER(c_char))), None)

        # compile the shader
        glCompileShader(shader)

        temp = c_int(0)
        # retrieve the compile status
        glGetShaderiv(shader, GL_COMPILE_STATUS, byref(temp))

        # if compilation failed, print the log
        if not temp:
            # retrieve the log length
            glGetShaderiv(shader, GL_INFO_LOG_LENGTH, byref(temp))
            # create a buffer for the log
            buffer = create_string_buffer(temp.value)
            # retrieve the log text
            glGetShaderInfoLog(shader, temp, None, buffer)
            # print the log to the console
            raise GLSLException(buffer.value)
        else:
            # all is well, so attach the shader to the program
            glAttachShader(self.handle, shader);

    def link(self):
        # link the program
        glLinkProgram(self.handle)

        temp = c_int(0)
        # retrieve the link status
        glGetProgramiv(self.handle, GL_LINK_STATUS, byref(temp))

        # if linking failed, print the log
        if not temp:
            #   retrieve the log length
            glGetProgramiv(self.handle, GL_INFO_LOG_LENGTH, byref(temp))
            # create a buffer for the log
            buffer = create_string_buffer(temp.value)
            # retrieve the log text
            glGetProgramInfoLog(self.handle, temp, None, buffer)
            # print the log to the console
            raise GLSLException(buffer.value)
        else:
            # all is well, so we are linked
            self.linked = True

    def bind(self):
        # bind the program
        glUseProgram(self.handle)

    @classmethod
    def unbind(self):
        # unbind whatever program is currently bound
        glUseProgram(0)

    def get_uniform_location(self, name):
        try:
            return self.location_cache[name]
        except KeyError:
            loc = glGetUniformLocation(self.handle, name)
            if loc == -1:
                raise GLSLException #TODO
            self.location_cache[name] = loc
            return loc

    # upload a floating point uniform
    # this program must be currently bound
    def uniformf(self, name, *vals):
        # check there are 1-4 values
        if len(vals) in range(1, 5):
            # select the correct function
            { 1 : glUniform1f,
                2 : glUniform2f,
                3 : glUniform3f,
                4 : glUniform4f
                # retrieve the uniform location, and set
            }[len(vals)](self.get_uniform_location(name), *vals)

    # upload an integer uniform
    # this program must be currently bound
    def uniformi(self, name, *vals):
        # check there are 1-4 values
        if len(vals) in range(1, 5):
            # select the correct function
            { 1 : glUniform1i,
                2 : glUniform2i,
                3 : glUniform3i,
                4 : glUniform4i
                # retrieve the uniform location, and set
            }[len(vals)](self.get_uniform_location(name), *vals)

    # upload a uniform matrix
    # works with matrices stored as lists,
    # as well as euclid matrices
    def uniform_matrixf(self, name, mat):
        # obtian the uniform location
        loc = self.get_uniform_location(name)
        # uplaod the 4x4 floating point matrix
        glUniformMatrix4fv(loc, 1, False, mat)

