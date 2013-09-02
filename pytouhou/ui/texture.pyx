# -*- encoding: utf-8 -*-
##
## Copyright (C) 2011 Thibaut Girka <thib@sitedethib.com>
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

from pytouhou.lib.opengl cimport \
         (glTexParameteri, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,
          GL_LINEAR, GL_BGRA, GL_RGBA, GL_RGB, GL_LUMINANCE, GL_UNSIGNED_BYTE,
          GL_UNSIGNED_SHORT_5_6_5, GL_UNSIGNED_SHORT_4_4_4_4_REV,
          glGenTextures, glBindTexture, glTexImage2D, GL_TEXTURE_2D, GLuint,
          glDeleteTextures)

from pytouhou.lib.sdl cimport load_png, create_rgb_surface
from pytouhou.formats.thtx import Texture #TODO: perhaps define that elsewhere?

import os


class TextureId(int):
    def __del__(self):
        cdef GLuint texture = self
        glDeleteTextures(1, &texture)
        self.renderer.remove_texture(self)


class TextureManager(object):
    def __init__(self, loader=None, renderer=None):
        self.loader = loader
        self.renderer = renderer


    def load(self, anm_list):
        for anm in sorted(anm_list, key=lambda x: x[0].first_name.endswith('ascii.png')):
            for entry in anm:
                if not hasattr(entry, 'texture'):
                    texture = decode_png(self.loader, entry.first_name, entry.secondary_name)
                    entry.texture = load_texture(texture)
                elif not isinstance(entry.texture, TextureId):
                    entry.texture = load_texture(entry.texture)
                self.renderer.add_texture(entry.texture)
                entry.texture.renderer = self.renderer


cdef decode_png(loader, first_name, secondary_name):
    image_file = load_png(loader.get_file(os.path.basename(first_name)))
    width, height = image_file.surface.w, image_file.surface.h

    # Support only 32 bits RGBA. Paletted surfaces are awful to work with.
    #TODO: verify it doesn’t blow up on big-endian systems.
    new_image = create_rgb_surface(width, height, 32, 0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000)
    new_image.blit(image_file)

    if secondary_name:
        alpha_file = load_png(loader.get_file(os.path.basename(secondary_name)))
        assert (width == alpha_file.surface.w and height == alpha_file.surface.h)

        new_alpha_file = create_rgb_surface(width, height, 24)
        new_alpha_file.blit(alpha_file)

        new_image.set_alpha(new_alpha_file)

    return Texture(width, height, -4, new_image.pixels)


cdef load_texture(thtx):
    cdef GLuint texture

    if thtx.fmt == 1:
        format_ = GL_BGRA
        type_ = GL_UNSIGNED_BYTE
        composants = GL_RGBA
    elif thtx.fmt == 3:
        format_ = GL_RGB
        type_ = GL_UNSIGNED_SHORT_5_6_5
        composants = GL_RGB
    elif thtx.fmt == 5:
        format_ = GL_BGRA
        type_ = GL_UNSIGNED_SHORT_4_4_4_4_REV
        composants = GL_RGBA
    elif thtx.fmt == 7:
        format_ = GL_LUMINANCE
        type_ = GL_UNSIGNED_BYTE
        composants = GL_LUMINANCE
    elif thtx.fmt == -4: #XXX: non-standard
        format_ = GL_RGBA
        type_ = GL_UNSIGNED_BYTE
        composants = GL_RGBA
    else:
        raise Exception('Unknown texture type')

    glGenTextures(1, &texture)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexImage2D(GL_TEXTURE_2D, 0,
                 composants,
                 thtx.width, thtx.height,
                 0,
                 format_, type_,
                 <char*>thtx.data)

    return TextureId(texture)
