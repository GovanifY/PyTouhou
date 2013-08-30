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
INIT_PNG = IMG_INIT_PNG

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

DEFAULT_FORMAT = MIX_DEFAULT_FORMAT


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
        if self.context == NULL:
            raise SDLError(SDL_GetError())

    def gl_swap_window(self):
        SDL_GL_SwapWindow(self.window)

    def gl_delete_context(self):
        SDL_GL_DeleteContext(self.context)

    def set_window_size(self, width, height):
        SDL_SetWindowSize(self.window, width, height)


cdef class Surface:
    cdef SDL_Surface *surface

    def __dealloc__(self):
        if self.surface != NULL:
            SDL_FreeSurface(self.surface)

    property width:
        def __get__(self):
            return self.surface.w

    property height:
        def __get__(self):
            return self.surface.h

    property pixels:
        def __get__(self):
            return bytes(self.surface.pixels[:self.surface.w * self.surface.h * 4])

    def blit(self, Surface other):
        if SDL_BlitSurface(other.surface, NULL, self.surface, NULL) < 0:
            raise SDLError(SDL_GetError())

    def set_alpha(self, Surface alpha_surface):
        nb_pixels = self.surface.w * self.surface.h
        image = self.surface.pixels
        alpha = alpha_surface.surface.pixels

        for i in xrange(nb_pixels):
            # Only use the red value, assume the others are equal.
            image[3+4*i] = alpha[3*i]


cdef class Music:
    cdef Mix_Music *music

    def __dealloc__(self):
        if self.music != NULL:
            Mix_FreeMusic(self.music)

    def play(self, int loops):
        Mix_PlayMusic(self.music, loops)

    def set_loop_points(self, double start, double end):
        #Mix_SetLoopPoints(self.music, start, end)
        pass


cdef class Chunk:
    cdef Mix_Chunk *chunk

    def __dealloc__(self):
        if self.chunk != NULL:
            Mix_FreeChunk(self.chunk)

    property volume:
        def __set__(self, float volume):
            Mix_VolumeChunk(self.chunk, int(volume * 128))

    def play(self, int channel, int loops):
        Mix_PlayChannel(channel, self.chunk, loops)


def init(Uint32 flags):
    if SDL_Init(flags) < 0:
        raise SDLError(SDL_GetError())


def img_init(Uint32 flags):
    if IMG_Init(flags) != flags:
        raise SDLError(SDL_GetError())


def mix_init(int flags):
    if Mix_Init(flags) != flags:
        raise SDLError(SDL_GetError())


IF UNAME_SYSNAME == "Windows":
    def set_main_ready():
        SDL_SetMainReady()


def quit():
    SDL_Quit()


def img_quit():
    IMG_Quit()


def mix_quit():
    Mix_Quit()


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


def load_png(file_):
    data = file_.read()
    rwops = SDL_RWFromConstMem(<char*>data, len(data))
    surface = Surface()
    surface.surface = IMG_LoadPNG_RW(rwops)
    SDL_RWclose(rwops)
    if surface.surface == NULL:
        raise SDLError(SDL_GetError())
    return surface


def create_rgb_surface(int width, int height, int depth, Uint32 rmask=0, Uint32 gmask=0, Uint32 bmask=0, Uint32 amask=0):
    surface = Surface()
    surface.surface = SDL_CreateRGBSurface(0, width, height, depth, rmask, gmask, bmask, amask)
    if surface.surface == NULL:
        raise SDLError(SDL_GetError())
    return surface


def mix_open_audio(int frequency, Uint16 format_, int channels, int chunksize):
    if Mix_OpenAudio(frequency, format_, channels, chunksize) < 0:
        raise SDLError(SDL_GetError())


def mix_close_audio():
    Mix_CloseAudio()


def mix_allocate_channels(int numchans):
    if Mix_AllocateChannels(numchans) != numchans:
        raise SDLError(SDL_GetError())


def mix_volume(int channel, float volume):
    return Mix_Volume(channel, int(volume * 128))


def mix_volume_music(float volume):
    return Mix_VolumeMusic(int(volume * 128))


def load_music(const char *filename):
    music = Music()
    music.music = Mix_LoadMUS(filename)
    if music.music == NULL:
        raise SDLError(SDL_GetError())
    return music


def load_chunk(file_):
    cdef SDL_RWops *rwops
    chunk = Chunk()
    data = file_.read()
    rwops = SDL_RWFromConstMem(<char*>data, len(data))
    chunk.chunk = Mix_LoadWAV_RW(rwops, 1)
    if chunk.chunk == NULL:
        raise SDLError(SDL_GetError())
    return chunk


def get_ticks():
    return SDL_GetTicks()


def delay(Uint32 ms):
    SDL_Delay(ms)
