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

from pytouhou.lib._sdl cimport *
cimport pytouhou.lib.gui as gui


cdef SDL_GLattr GL_CONTEXT_MAJOR_VERSION
cdef SDL_GLattr GL_CONTEXT_MINOR_VERSION
cdef SDL_GLattr GL_CONTEXT_PROFILE_MASK
cdef SDL_GLattr GL_DOUBLEBUFFER
cdef SDL_GLattr GL_RED_SIZE
cdef SDL_GLattr GL_GREEN_SIZE
cdef SDL_GLattr GL_BLUE_SIZE
cdef SDL_GLattr GL_DEPTH_SIZE

cdef SDL_GLprofile GL_CONTEXT_PROFILE_CORE
cdef SDL_GLprofile GL_CONTEXT_PROFILE_COMPATIBILITY
cdef SDL_GLprofile GL_CONTEXT_PROFILE_ES

cdef SDL_WindowFlags WINDOWPOS_CENTERED
cdef SDL_WindowFlags WINDOW_OPENGL
cdef SDL_WindowFlags WINDOW_SHOWN
cdef SDL_WindowFlags WINDOW_RESIZABLE

#TODO: should be SDL_Scancode, but Cython doesn’t allow enum for array indexing.
cdef long SCANCODE_Z
cdef long SCANCODE_X
cdef long SCANCODE_P
cdef long SCANCODE_LSHIFT
cdef long SCANCODE_UP
cdef long SCANCODE_DOWN
cdef long SCANCODE_LEFT
cdef long SCANCODE_RIGHT
cdef long SCANCODE_LCTRL
cdef long SCANCODE_ESCAPE
cdef long SCANCODE_HOME

cdef SDL_WindowEventID WINDOWEVENT_RESIZED

cdef SDL_EventType KEYDOWN
cdef SDL_EventType QUIT
cdef SDL_EventType WINDOWEVENT

cdef const Uint8 *keyboard_state


cdef class Window(gui.Window):
    cdef SDL_Window *window
    cdef SDL_GLContext context
    cdef SDL_Renderer *renderer
    cdef bint is_fullscreen

    # The following functions are there for the pure SDL backend.
    cdef bint create_renderer(self, Uint32 flags) except True
    cdef bint render_clear(self) except True
    cdef bint render_copy(self, Texture texture, Rect srcrect, Rect dstrect) except True
    cdef bint render_copy_ex(self, Texture texture, Rect srcrect, Rect dstrect, double angle, bint flip) except True
    cdef bint render_set_clip_rect(self, Rect rect) except True
    cdef bint render_set_viewport(self, Rect rect) except True
    cdef Texture create_texture_from_surface(self, Surface surface)


cdef class Texture:
    cdef SDL_Texture *texture

    cpdef set_color_mod(self, Uint8 r, Uint8 g, Uint8 b)
    cpdef set_alpha_mod(self, Uint8 alpha)
    cpdef set_blend_mode(self, SDL_BlendMode blend_mode)


cdef class Rect:
    cdef SDL_Rect rect


cdef class Color:
    cdef SDL_Color color


cdef class Surface:
    cdef SDL_Surface *surface

    cdef bint blit(self, Surface other) except True
    cdef void set_alpha(self, Surface alpha_surface) nogil


cdef class Music:
    cdef Mix_Music *music

    cdef void play(self, int loops) nogil
    cdef void set_loop_points(self, double start, double end) nogil


cdef class Chunk:
    cdef Mix_Chunk *chunk

    cdef void play(self, int channel, int loops) nogil
    cdef void set_volume(self, float volume) nogil


cdef class Font:
    cdef TTF_Font *font

    cdef Surface render(self, unicode text)


cdef bint init(Uint32 flags) except True
cdef bint img_init(int flags) except True
cdef bint mix_init(int flags) except True
cdef bint ttf_init() except True
cdef bint gl_set_attribute(SDL_GLattr attr, int value) except True
cdef Surface load_png(file_)
cdef Surface create_rgb_surface(int width, int height, int depth, Uint32 rmask=*, Uint32 gmask=*, Uint32 bmask=*, Uint32 amask=*)
cdef bint mix_open_audio(int frequency, Uint16 format_, int channels, int chunksize) except True
cdef bint mix_allocate_channels(int numchans) except True
cdef int mix_volume(int channel, float volume) nogil
cdef int mix_volume_music(float volume) nogil
cdef Music load_music(str filename)
cdef Chunk load_chunk(file_)
cdef Uint32 get_ticks() nogil
cdef void delay(Uint32 ms) nogil
cpdef bint show_simple_message_box(unicode message) except True
