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

from _sdl cimport *


cdef Uint32 INIT_VIDEO
cdef Uint32 INIT_PNG

cdef SDL_GLattr GL_CONTEXT_MAJOR_VERSION
cdef SDL_GLattr GL_CONTEXT_MINOR_VERSION
cdef SDL_GLattr GL_DOUBLEBUFFER
cdef SDL_GLattr GL_DEPTH_SIZE

cdef SDL_WindowFlags WINDOWPOS_CENTERED
cdef SDL_WindowFlags WINDOW_OPENGL
cdef SDL_WindowFlags WINDOW_SHOWN

#TODO: should be SDL_Scancode, but Cython doesn’t allow enum for array indexing.
cdef long SCANCODE_Z
cdef long SCANCODE_X
cdef long SCANCODE_LSHIFT
cdef long SCANCODE_UP
cdef long SCANCODE_DOWN
cdef long SCANCODE_LEFT
cdef long SCANCODE_RIGHT
cdef long SCANCODE_LCTRL
cdef long SCANCODE_ESCAPE

cdef SDL_EventType KEYDOWN
cdef SDL_EventType QUIT

cdef Uint16 DEFAULT_FORMAT


cdef class Window:
    cdef SDL_Window *window
    cdef SDL_GLContext context

    cdef void gl_create_context(self) except *
    cdef void gl_swap_window(self) nogil
    cdef void set_window_size(self, int width, int height) nogil


cdef class Surface:
    cdef SDL_Surface *surface

    cdef void blit(self, Surface other) except *
    cdef void set_alpha(self, Surface alpha_surface) nogil


cdef class Music:
    cdef Mix_Music *music

    cdef void play(self, int loops) nogil
    cdef void set_loop_points(self, double start, double end) nogil


cdef class Chunk:
    cdef Mix_Chunk *chunk

    cdef void play(self, int channel, int loops) nogil
    cdef void set_volume(self, float volume) nogil


cdef void init(Uint32 flags) except *
cdef void img_init(Uint32 flags) except *
cdef void mix_init(int flags) except *

IF UNAME_SYSNAME == "Windows":
    cdef void set_main_ready()

cdef void quit() nogil
cdef void img_quit() nogil
cdef void mix_quit() nogil
cdef void gl_set_attribute(SDL_GLattr attr, int value) except *
cdef list poll_events()
cdef const Uint8* get_keyboard_state() nogil
cdef Surface load_png(file_)
cdef Surface create_rgb_surface(int width, int height, int depth, Uint32 rmask=*, Uint32 gmask=*, Uint32 bmask=*, Uint32 amask=*)
cdef void mix_open_audio(int frequency, Uint16 format_, int channels, int chunksize) except *
cdef void mix_close_audio() nogil
cdef void mix_allocate_channels(int numchans) except *
cdef int mix_volume(int channel, float volume) nogil
cdef int mix_volume_music(float volume) nogil
cdef Music load_music(const char *filename)
cdef Chunk load_chunk(file_)
cdef Uint32 get_ticks() nogil
cdef void delay(Uint32 ms) nogil
