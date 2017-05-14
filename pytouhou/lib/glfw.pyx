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

from .gui cimport SHOOT, BOMB, FOCUS, UP, DOWN, LEFT, RIGHT, SKIP

CLIENT_API = GLFW_CLIENT_API
OPENGL_PROFILE = GLFW_OPENGL_PROFILE
CONTEXT_VERSION_MAJOR = GLFW_CONTEXT_VERSION_MAJOR
CONTEXT_VERSION_MINOR = GLFW_CONTEXT_VERSION_MINOR
DEPTH_BITS = GLFW_DEPTH_BITS
ALPHA_BITS = GLFW_ALPHA_BITS
RESIZABLE = GLFW_RESIZABLE
DOUBLEBUFFER = GLFW_DOUBLEBUFFER

OPENGL_API = GLFW_OPENGL_API
OPENGL_ES_API = GLFW_OPENGL_ES_API
OPENGL_CORE_PROFILE = GLFW_OPENGL_CORE_PROFILE

cdef void error_callback(int a, const char* b):
    print('GLFW error 0x%x: %s' % (a, b.decode('utf-8')))

cdef list _global_events = []

cdef void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods):
    if action != GLFW_PRESS:
        return
    if key == GLFW_KEY_ESCAPE:
        _global_events.append((gui.PAUSE, None))
    elif key in (GLFW_KEY_P, GLFW_KEY_HOME):
        _global_events.append((gui.SCREENSHOT, None))
    elif key == GLFW_KEY_DOWN:
        _global_events.append((gui.DOWN, None))
    elif key == GLFW_KEY_F11:
        _global_events.append((gui.FULLSCREEN, None))
    elif key == GLFW_KEY_ENTER:
        if mods & GLFW_MOD_ALT:
            _global_events.append((gui.FULLSCREEN, None))

cdef void size_callback(GLFWwindow* window, int width, int height):
    _global_events.append((gui.RESIZE, (width, height)))

cdef void close_callback(GLFWwindow* window):
    _global_events.append((gui.EXIT, None))

cdef void init() except *:
    glfwSetErrorCallback(<GLFWerrorfun>error_callback)
    ret = glfwInit()
    if not ret:
        raise Exception('TODO')

cdef void terminate() nogil:
    glfwTerminate()

cdef void window_hint(int hint, int value) nogil:
    glfwWindowHint(hint, value)

cdef class Window:
    def __init__(self, int width, int height, str title, Monitor monitor=None, Window share=None):
        cdef GLFWmonitor* c_monitor = NULL
        cdef GLFWwindow* c_share = NULL
        if monitor is not None:
            c_monitor = monitor.monitor
        if share is not None:
            c_share = share.window
        self.window = glfwCreateWindow(width, height, title.encode('utf-8'), c_monitor, c_share)
        if self.window == NULL:
            raise Exception('TODO')
        glfwSetFramebufferSizeCallback(self.window, <GLFWframebuffersizefun>size_callback)
        glfwSetWindowCloseCallback(self.window, <GLFWwindowclosefun>close_callback)
        glfwSetKeyCallback(self.window, <GLFWkeyfun>key_callback)

    def __del__(self):
        glfwDestroyWindow(self.window)

    cdef void create_gl_context(self) except *:
        glfwMakeContextCurrent(self.window)

    cdef void present(self) nogil:
        glfwSwapBuffers(self.window)

    cdef void set_window_size(self, int width, int height) nogil:
        pass

    cdef list get_events(self):
        glfwPollEvents()
        events = _global_events[:]
        _global_events.clear()
        return events

    cdef void toggle_fullscreen(self) nogil:
        monitor = glfwGetWindowMonitor(self.window)
        if monitor == NULL:
            monitor = glfwGetPrimaryMonitor()
        else:
            monitor = NULL
        # TODO: save the previous size.
        glfwSetWindowMonitor(self.window, monitor, 0, 0, 640, 480, 60)

    cdef int get_keystate(self) nogil:
        cdef int keystate = 0
        if glfwGetKey(self.window, GLFW_KEY_Z):
            keystate |= SHOOT
        if glfwGetKey(self.window, GLFW_KEY_X):
            keystate |= BOMB
        if glfwGetKey(self.window, GLFW_KEY_LEFT_SHIFT):
            keystate |= FOCUS
        if glfwGetKey(self.window, GLFW_KEY_UP):
            keystate |= UP
        if glfwGetKey(self.window, GLFW_KEY_DOWN):
            keystate |= DOWN
        if glfwGetKey(self.window, GLFW_KEY_LEFT):
            keystate |= LEFT
        if glfwGetKey(self.window, GLFW_KEY_RIGHT):
            keystate |= RIGHT
        if glfwGetKey(self.window, GLFW_KEY_LEFT_CONTROL):
            keystate |= SKIP
        return keystate
