# -*- encoding: utf-8 -*-
##
## Copyright (C) 2016 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from .backend cimport profile, major, minor, double_buffer, is_legacy

cimport pytouhou.lib.glfw as glfw


def create_glfw_window(title, width, height):
    '''Create a window (using GLFW) and an OpenGL context.'''

    glfw.init()

    if profile == 'core':
        glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    elif profile == 'es':
        glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_ES_API)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, major)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, minor)
    glfw.window_hint(glfw.ALPHA_BITS, 0)
    glfw.window_hint(glfw.DEPTH_BITS, 24 if is_legacy else 0)
    if double_buffer >= 0:
        glfw.window_hint(glfw.DOUBLEBUFFER, double_buffer)

    # Legacy contexts don’t support our required extensions for scaling.
    if not is_legacy:
        glfw.window_hint(glfw.RESIZABLE, True)

    return glfw.Window(width, height, title)
