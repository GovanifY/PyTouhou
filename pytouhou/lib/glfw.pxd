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

from pytouhou.lib._glfw cimport *
cimport pytouhou.lib.gui as gui

cdef int CLIENT_API
cdef int OPENGL_PROFILE
cdef int CONTEXT_VERSION_MAJOR
cdef int CONTEXT_VERSION_MINOR
cdef int DEPTH_BITS
cdef int ALPHA_BITS
cdef int RESIZABLE
cdef int DOUBLEBUFFER

cdef int OPENGL_API
cdef int OPENGL_ES_API
cdef int OPENGL_CORE_PROFILE

cdef void init() except *
cdef void terminate() nogil
cdef void window_hint(int hint, int value) nogil

cdef class Window(gui.Window):
    cdef GLFWwindow* window

cdef class Monitor:
    cdef GLFWmonitor* monitor
