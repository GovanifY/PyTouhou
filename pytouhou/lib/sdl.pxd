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

cdef extern from "SDL.h":
    ctypedef unsigned int Uint32
    ctypedef unsigned short Uint16
    ctypedef unsigned char Uint8

    int SDL_INIT_VIDEO

    int SDL_Init(Uint32 flags)
    void SDL_Quit()


cdef extern from "SDL_error.h":
    const char *SDL_GetError()


cdef extern from "SDL_video.h":
    ctypedef enum SDL_GLattr:
        SDL_GL_CONTEXT_MAJOR_VERSION
        SDL_GL_CONTEXT_MINOR_VERSION
        SDL_GL_DOUBLEBUFFER
        SDL_GL_DEPTH_SIZE

    ctypedef enum SDL_WindowFlags:
        SDL_WINDOWPOS_CENTERED
        SDL_WINDOW_OPENGL
        SDL_WINDOW_SHOWN

    ctypedef struct SDL_Window:
        pass

    ctypedef void *SDL_GLContext

    int SDL_GL_SetAttribute(SDL_GLattr attr, int value)
    SDL_Window *SDL_CreateWindow(const char *title, int x, int y, int w, int h, Uint32 flags)
    SDL_GLContext SDL_GL_CreateContext(SDL_Window *window)
    void SDL_GL_SwapWindow(SDL_Window *window)
    void SDL_GL_DeleteContext(SDL_GLContext context)
    void SDL_DestroyWindow(SDL_Window *window)


cdef extern from "SDL_scancode.h":
    ctypedef enum SDL_Scancode:
        SDL_SCANCODE_Z
        SDL_SCANCODE_X
        SDL_SCANCODE_LSHIFT
        SDL_SCANCODE_UP
        SDL_SCANCODE_DOWN
        SDL_SCANCODE_LEFT
        SDL_SCANCODE_RIGHT
        SDL_SCANCODE_LCTRL
        SDL_SCANCODE_ESCAPE


cdef extern from "SDL_events.h":
    ctypedef enum SDL_EventType:
        SDL_KEYDOWN
        SDL_QUIT

    ctypedef struct SDL_Keysym:
        SDL_Scancode scancode

    ctypedef struct SDL_KeyboardEvent:
        Uint32 type
        SDL_Keysym keysym

    ctypedef union SDL_Event:
        Uint32 type
        SDL_KeyboardEvent key

    int SDL_PollEvent(SDL_Event *event)


cdef extern from "SDL_keyboard.h":
    const Uint8 *SDL_GetKeyboardState(int *numkeys)
