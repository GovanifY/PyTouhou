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

from pyglet.gl import (glTexParameteri, GL_TEXTURE_MIN_FILTER,
                       GL_TEXTURE_MAG_FILTER, GL_LINEAR, GL_BGRA, GL_RGBA,
                       GL_RGB, GL_LUMINANCE, GL_UNSIGNED_BYTE,
                       GL_UNSIGNED_SHORT_5_6_5, GL_UNSIGNED_SHORT_4_4_4_4_REV,
                       glGenTextures, glBindTexture, glTexImage2D,
                       GL_TEXTURE_2D)
from ctypes import c_uint, byref
from pytouhou.lib.sdl import load_png, create_rgb_surface
import os

from pytouhou.formats.thtx import Texture #TODO: perhaps define that elsewhere?


cdef class TextureManager:
    def __init__(self, loader=None):
        self.loader = loader
        self.textures = {}


    def __getitem__(self, key):
        if not key in self.textures:
            self.textures[key] = self.load_texture(key)
        return self.textures[key]


    def preload(self, anm_wrapper):
        for anm in anm_wrapper:
            anm.texture = self.load_png_texture(anm.first_name, anm.secondary_name)


    def load_png_texture(self, first_name, secondary_name):
        image_file = load_png(self.loader.get_file(os.path.basename(first_name)))
        width, height = image_file.width, image_file.height

        # Support only 32 bits RGBA. Paletted surfaces are awful to work with.
        #TODO: verify it doesn’t blow up on big-endian systems.
        new_image = create_rgb_surface(width, height, 32, 0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000)
        new_image.blit(image_file)

        if secondary_name:
            alpha_file = load_png(self.loader.get_file(os.path.basename(secondary_name)))
            assert (width == alpha_file.width and
                    height == alpha_file.height)

            new_alpha_file = create_rgb_surface(width, height, 24)
            new_alpha_file.blit(alpha_file)

            new_image.set_alpha(new_alpha_file)

        return Texture(width, height, -4, new_image.pixels)


    def load_texture(self, key):
        if not isinstance(key, Texture):
            first_name, secondary_name = key
            key = self.load_png_texture(first_name, secondary_name)

        if key.fmt == 1:
            format_ = GL_BGRA
            type_ = GL_UNSIGNED_BYTE
            composants = GL_RGBA
        elif key.fmt == 3:
            format_ = GL_RGB
            type_ = GL_UNSIGNED_SHORT_5_6_5
            composants = GL_RGB
        elif key.fmt == 5:
            format_ = GL_BGRA
            type_ = GL_UNSIGNED_SHORT_4_4_4_4_REV
            composants = GL_RGBA
        elif key.fmt == 7:
            format_ = GL_LUMINANCE
            type_ = GL_UNSIGNED_BYTE
            composants = GL_LUMINANCE
        elif key.fmt == -4: #XXX: non-standard
            format_ = GL_RGBA
            type_ = GL_UNSIGNED_BYTE
            composants = GL_RGBA
        else:
            raise Exception('Unknown texture type')

        id_ = c_uint()
        glGenTextures(1, byref(id_))
        glBindTexture(GL_TEXTURE_2D, id_.value)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glTexImage2D(GL_TEXTURE_2D, 0,
                     composants,
                     key.width, key.height,
                     0,
                     format_, type_,
                     key.data)

        return id_.value
