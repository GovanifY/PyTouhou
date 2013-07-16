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

    void SDL_SetWindowSize(SDL_Window *window, int w, int h)


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


cdef extern from "SDL_timer.h":
    Uint32 SDL_GetTicks()
    void SDL_Delay(Uint32 ms)


cdef extern from "SDL_rect.h":
    ctypedef struct SDL_Rect:
        int x, y
        int w, h


cdef extern from "SDL_surface.h":
    ctypedef struct SDL_Surface:
        int w, h
        unsigned char *pixels

    void SDL_FreeSurface(SDL_Surface *surface)
    int SDL_BlitSurface(SDL_Surface *src, const SDL_Rect *srcrect, SDL_Surface *dst, SDL_Rect *dstrect)
    SDL_Surface *SDL_CreateRGBSurface(Uint32 flags, int width, int height, int depth, Uint32 Rmask, Uint32 Gmask, Uint32 Bmask, Uint32 Amask)


cdef extern from "SDL_rwops.h":
    ctypedef struct SDL_RWops:
        pass

    SDL_RWops *SDL_RWFromConstMem(const void *mem, int size)
    int SDL_RWclose(SDL_RWops *context)


cdef extern from "SDL_image.h":
    int IMG_INIT_PNG

    int IMG_Init(int flags)
    void IMG_Quit()
    SDL_Surface *IMG_LoadPNG_RW(SDL_RWops *src)


cdef extern from "SDL_mixer.h":
    ctypedef enum:
        MIX_DEFAULT_FORMAT

    ctypedef struct Mix_Music:
        pass

    ctypedef struct Mix_Chunk:
        pass

    int Mix_Init(int flags)
    void Mix_Quit()

    int Mix_OpenAudio(int frequency, Uint16 format_, int channels, int chunksize)
    void Mix_CloseAudio()

    int Mix_AllocateChannels(int numchans)

    Mix_Music *Mix_LoadMUS(const char *filename)
    Mix_Chunk *Mix_LoadWAV_RW(SDL_RWops *src, int freesrc)

    void Mix_FreeMusic(Mix_Music *music)
    void Mix_FreeChunk(Mix_Chunk *chunk)

    int Mix_PlayMusic(Mix_Music *music, int loops)
    #int Mix_SetLoopPoints(Mix_Music *music, double start, double end)

    int Mix_Volume(int channel, int volume)
    int Mix_VolumeChunk(Mix_Chunk *chunk, int volume)
    int Mix_VolumeMusic(int volume)

    int Mix_PlayChannel(int channel, Mix_Chunk *chunk, int loops)
