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

import pyglet
from pyglet.gl import (glTexParameteri,
                       GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
import os


cdef class TextureManager:
    def __init__(self, loader=None):
        self.loader = loader
        self.textures = {}


    def __getitem__(self, key):
        if not key in self.textures:
            self.textures[key] = self.load_texture(key)
        return self.textures[key]


    def preload(self, anm_wrapper):
        try:
            anms = anm_wrapper.anm_files
        except AttributeError:
            anms = anm_wrapper

        for anm in anms:
            key = anm.first_name, anm.secondary_name
            texture = self[key]


    def load_texture(self, key):
        first_name, secondary_name = key

        image_file = pyglet.image.load(first_name, file=self.loader.get_file(os.path.basename(first_name)))

        if secondary_name:
            alpha_file = pyglet.image.load(secondary_name, file=self.loader.get_file(os.path.basename(secondary_name)))
            assert (image_file.width, image_file.height) == (alpha_file.width, image_file.height)

            data = image_file.get_data('RGB', image_file.width * 3)
            alpha_data = alpha_file.get_data('RGB', image_file.width * 3)
            image_file = pyglet.image.ImageData(image_file.width, image_file.height, 'RGBA', b''.join(data[i*3:i*3+3] + alpha_data[i*3] for i in range(image_file.width * image_file.height)))

            #TODO: improve perfs somehow

        texture = image_file.get_texture()

        glTexParameteri(texture.target, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(texture.target, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        return texture

