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

INIT_VIDEO = SDL_INIT_VIDEO

GL_CONTEXT_MAJOR_VERSION = SDL_GL_CONTEXT_MAJOR_VERSION
GL_CONTEXT_MINOR_VERSION = SDL_GL_CONTEXT_MINOR_VERSION
GL_DOUBLEBUFFER = SDL_GL_DOUBLEBUFFER
GL_DEPTH_SIZE = SDL_GL_DEPTH_SIZE

WINDOWPOS_CENTERED = SDL_WINDOWPOS_CENTERED
WINDOW_OPENGL = SDL_WINDOW_OPENGL
WINDOW_SHOWN = SDL_WINDOW_SHOWN

SCANCODE_Z = SDL_SCANCODE_Z
SCANCODE_X = SDL_SCANCODE_X
SCANCODE_LSHIFT = SDL_SCANCODE_LSHIFT
SCANCODE_UP = SDL_SCANCODE_UP
SCANCODE_DOWN = SDL_SCANCODE_DOWN
SCANCODE_LEFT = SDL_SCANCODE_LEFT
SCANCODE_RIGHT = SDL_SCANCODE_RIGHT
SCANCODE_LCTRL = SDL_SCANCODE_LCTRL
SCANCODE_ESCAPE = SDL_SCANCODE_ESCAPE

KEYDOWN = SDL_KEYDOWN
QUIT = SDL_QUIT


class SDLError(Exception):
    pass


cdef class Window:
    cdef SDL_Window *window
    cdef SDL_GLContext context

    def __init__(self, const char *title, int x, int y, int w, int h, Uint32 flags):
        self.window = SDL_CreateWindow(title, x, y, w, h, flags)
        if self.window == NULL:
            raise SDLError(SDL_GetError())

    def destroy_window(self):
        SDL_DestroyWindow(self.window)

    def gl_create_context(self):
        self.context = SDL_GL_CreateContext(self.window)

    def gl_swap_window(self):
        SDL_GL_SwapWindow(self.window)

    def gl_delete_context(self):
        SDL_GL_DeleteContext(self.context)


def init(Uint32 flags):
    if SDL_Init(flags) < 0:
        raise SDLError(SDL_GetError())


def quit():
    SDL_Quit()


def gl_set_attribute(SDL_GLattr attr, int value):
    if SDL_GL_SetAttribute(attr, value) < 0:
        raise SDLError(SDL_GetError())


def poll_events():
    cdef SDL_Event event
    ret = []
    while SDL_PollEvent(&event):
        if event.type == SDL_KEYDOWN:
            ret.append((event.type, event.key.keysym.scancode))
        elif event.type == SDL_QUIT:
            ret.append((event.type,))
    return ret


def get_keyboard_state():
    cdef int numkeys
    cdef bint k
    cdef const Uint8 *state
    state = SDL_GetKeyboardState(&numkeys)
    return tuple([k is not False for k in state[:numkeys]])


def get_ticks():
    return SDL_GetTicks()


def delay(Uint32 ms):
    SDL_Delay(ms)
