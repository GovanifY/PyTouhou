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

cdef extern from "SDL.h" nogil:
    ctypedef unsigned int Uint32
    ctypedef unsigned short Uint16
    ctypedef unsigned char Uint8

    int SDL_INIT_VIDEO

    int SDL_Init(Uint32 flags)
    void SDL_Quit()


IF UNAME_SYSNAME == "Windows":
    cdef extern from "SDL_main.h" nogil:
        void SDL_SetMainReady()


cdef extern from "SDL_error.h" nogil:
    const char *SDL_GetError()


cdef extern from "SDL_video.h" nogil:
    ctypedef enum SDL_GLattr:
        SDL_GL_CONTEXT_MAJOR_VERSION
        SDL_GL_CONTEXT_MINOR_VERSION
        SDL_GL_CONTEXT_PROFILE_MASK
        SDL_GL_DOUBLEBUFFER
        SDL_GL_RED_SIZE
        SDL_GL_GREEN_SIZE
        SDL_GL_BLUE_SIZE
        SDL_GL_DEPTH_SIZE

    ctypedef enum SDL_GLprofile:
        SDL_GL_CONTEXT_PROFILE_CORE
        SDL_GL_CONTEXT_PROFILE_COMPATIBILITY
        SDL_GL_CONTEXT_PROFILE_ES

    ctypedef enum SDL_WindowFlags:
        SDL_WINDOWPOS_CENTERED
        SDL_WINDOW_OPENGL
        SDL_WINDOW_RESIZABLE
        SDL_WINDOW_FULLSCREEN_DESKTOP

    ctypedef struct SDL_Window:
        pass

    ctypedef void *SDL_GLContext

    int SDL_GL_SetAttribute(SDL_GLattr attr, int value)
    int SDL_GL_SetSwapInterval(int interval)
    SDL_Window *SDL_CreateWindow(const char *title, int x, int y, int w, int h, Uint32 flags)
    SDL_GLContext SDL_GL_CreateContext(SDL_Window *window)
    void SDL_GL_SwapWindow(SDL_Window *window)
    void SDL_GL_DeleteContext(SDL_GLContext context)
    void SDL_DestroyWindow(SDL_Window *window)

    void SDL_SetWindowSize(SDL_Window *window, int w, int h)
    int SDL_SetWindowFullscreen(SDL_Window *window, Uint32 flags)


cdef extern from "SDL_scancode.h" nogil:
    ctypedef enum SDL_Scancode:
        SDL_SCANCODE_Z
        SDL_SCANCODE_X
        SDL_SCANCODE_P
        SDL_SCANCODE_LSHIFT
        SDL_SCANCODE_UP
        SDL_SCANCODE_DOWN
        SDL_SCANCODE_LEFT
        SDL_SCANCODE_RIGHT
        SDL_SCANCODE_LCTRL
        SDL_SCANCODE_ESCAPE
        SDL_SCANCODE_HOME
        SDL_SCANCODE_RETURN
        SDL_SCANCODE_F11


cdef extern from "SDL_keycode.h" nogil:
    ctypedef enum SDL_Keymod:
        KMOD_ALT


cdef extern from "SDL_events.h" nogil:
    ctypedef enum SDL_EventType:
        SDL_KEYDOWN
        SDL_QUIT
        SDL_WINDOWEVENT

    ctypedef struct SDL_Keysym:
        SDL_Scancode scancode
        Uint16 mod

    ctypedef struct SDL_KeyboardEvent:
        Uint32 type
        SDL_Keysym keysym

    ctypedef enum SDL_WindowEventID:
        SDL_WINDOWEVENT_RESIZED

    ctypedef struct SDL_WindowEvent:
        Uint32 type
        SDL_WindowEventID event
        int data1
        int data2

    ctypedef union SDL_Event:
        Uint32 type
        SDL_KeyboardEvent key
        SDL_WindowEvent window

    int SDL_PollEvent(SDL_Event *event)


cdef extern from "SDL_keyboard.h" nogil:
    const Uint8 *SDL_GetKeyboardState(int *numkeys)


cdef extern from "SDL_timer.h" nogil:
    Uint32 SDL_GetTicks()
    void SDL_Delay(Uint32 ms)


cdef extern from "SDL_rect.h" nogil:
    ctypedef struct SDL_Rect:
        int x, y
        int w, h


cdef extern from "SDL_surface.h" nogil:
    ctypedef struct SDL_Surface:
        int w, h
        unsigned char *pixels

    void SDL_FreeSurface(SDL_Surface *surface)
    int SDL_BlitSurface(SDL_Surface *src, const SDL_Rect *srcrect, SDL_Surface *dst, SDL_Rect *dstrect)
    SDL_Surface *SDL_CreateRGBSurface(Uint32 flags, int width, int height, int depth, Uint32 Rmask, Uint32 Gmask, Uint32 Bmask, Uint32 Amask)


cdef extern from "SDL_rwops.h" nogil:
    ctypedef struct SDL_RWops:
        pass

    SDL_RWops *SDL_RWFromConstMem(const void *mem, int size)
    int SDL_RWclose(SDL_RWops *context)


cdef extern from "SDL_image.h" nogil:
    int IMG_INIT_PNG

    int IMG_Init(int flags)
    void IMG_Quit()
    SDL_Surface *IMG_LoadPNG_RW(SDL_RWops *src)


cdef extern from "SDL_mixer.h" nogil:
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


cdef extern from "SDL_pixels.h" nogil:
    ctypedef struct SDL_Color:
        Uint8 r, g, b, a


cdef extern from "SDL_ttf.h" nogil:
    ctypedef struct TTF_Font:
        pass

    int TTF_Init()
    void TTF_Quit()
    TTF_Font *TTF_OpenFont(const char *filename, int ptsize)
    void TTF_CloseFont(TTF_Font *font)
    SDL_Surface *TTF_RenderUTF8_Blended(TTF_Font *font, const char *text, SDL_Color fg)


cdef extern from "SDL_messagebox.h" nogil:
    int SDL_ShowSimpleMessageBox(Uint32 flags, const char *title, const char *message, SDL_Window *window)


cdef extern from "SDL_blendmode.h" nogil:
    ctypedef enum SDL_BlendMode:
        SDL_BLENDMODE_NONE
        SDL_BLENDMODE_BLEND
        SDL_BLENDMODE_ADD
        SDL_BLENDMODE_MOD


cdef extern from "SDL_render.h" nogil:
    ctypedef struct SDL_Renderer:
        pass

    ctypedef struct SDL_Texture:
        pass

    ctypedef struct SDL_Point:
        pass

    SDL_Renderer *SDL_CreateRenderer(SDL_Window *window, int index, Uint32 flags)
    void SDL_RenderPresent(SDL_Renderer *renderer)
    int SDL_RenderClear(SDL_Renderer *renderer)
    SDL_Texture *SDL_CreateTextureFromSurface(SDL_Renderer *renderer, SDL_Surface *surface)
    int SDL_RenderCopy(SDL_Renderer *renderer, SDL_Texture *texture, const SDL_Rect *srcrect, const SDL_Rect *dstrect)
    int SDL_RenderCopyEx(SDL_Renderer *renderer, SDL_Texture *texture, const SDL_Rect *srcrect, const SDL_Rect *dstrect, double angle, const SDL_Point *center, bint flip)
    int SDL_RenderSetClipRect(SDL_Renderer *renderer, const SDL_Rect *rect)
    int SDL_RenderSetViewport(SDL_Renderer *renderer, const SDL_Rect *rect)

    int SDL_SetTextureColorMod(SDL_Texture *texture, Uint8 r, Uint8 g, Uint8 b)
    int SDL_SetTextureAlphaMod(SDL_Texture *texture, Uint8 alpha)
    int SDL_SetTextureBlendMode(SDL_Texture *texture, SDL_BlendMode blend_mode)
