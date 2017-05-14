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

cdef extern from "GLFW/glfw3.h" nogil:
    ctypedef void* GLFWmonitor
    ctypedef void* GLFWwindow

    ctypedef void (* GLFWerrorfun)(int, const char*)
    ctypedef void (* GLFWwindowclosefun)(GLFWwindow*)
    ctypedef void (* GLFWframebuffersizefun)(GLFWwindow*,int,int)
    ctypedef void (* GLFWkeyfun)(GLFWwindow*, int, int, int, int)

    int glfwInit()
    void glfwTerminate()

    GLFWerrorfun glfwSetErrorCallback(GLFWerrorfun cbfun)

    void glfwWindowHint(int hint, int value)
    GLFWwindow* glfwCreateWindow(int width, int height, const char* title, GLFWmonitor* monitor, GLFWwindow* share)
    void glfwDestroyWindow(GLFWwindow* window)
    void glfwSetWindowShouldClose(GLFWwindow* window, int value)

    GLFWmonitor* glfwGetPrimaryMonitor()
    GLFWmonitor* glfwGetWindowMonitor(GLFWwindow* window)
    void glfwSetWindowMonitor(GLFWwindow* window, GLFWmonitor* monitor, int xpos, int ypos, int width, int height, int refreshRate)

    GLFWwindowclosefun glfwSetWindowCloseCallback(GLFWwindow* window, GLFWwindowclosefun cbfun)
    GLFWframebuffersizefun glfwSetFramebufferSizeCallback(GLFWwindow* window, GLFWframebuffersizefun cbfun)
    void glfwPollEvents()

    bint glfwGetKey(GLFWwindow* window, int key)
    GLFWkeyfun glfwSetKeyCallback(GLFWwindow* window, GLFWkeyfun cbfun)

    void glfwMakeContextCurrent(GLFWwindow* window)
    void glfwSwapBuffers(GLFWwindow* window)

    ctypedef enum:
        GLFW_DONT_CARE

    ctypedef enum:
        GLFW_KEY_Z
        GLFW_KEY_X
        GLFW_KEY_P
        GLFW_KEY_LEFT_SHIFT
        GLFW_KEY_UP
        GLFW_KEY_DOWN
        GLFW_KEY_LEFT
        GLFW_KEY_RIGHT
        GLFW_KEY_LEFT_CONTROL
        GLFW_KEY_ESCAPE
        GLFW_KEY_HOME
        GLFW_KEY_ENTER
        GLFW_KEY_F11

    ctypedef enum:
        GLFW_MOD_ALT

    ctypedef enum:
        GLFW_PRESS

    ctypedef enum:
        GLFW_CLIENT_API
        GLFW_OPENGL_PROFILE
        GLFW_CONTEXT_VERSION_MAJOR
        GLFW_CONTEXT_VERSION_MINOR
        GLFW_DEPTH_BITS
        GLFW_ALPHA_BITS
        GLFW_DOUBLEBUFFER
        GLFW_RESIZABLE

    ctypedef enum:
        GLFW_OPENGL_API
        GLFW_OPENGL_ES_API
        GLFW_OPENGL_CORE_PROFILE
