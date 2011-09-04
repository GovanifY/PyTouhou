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

import pygame
import os
from io import BytesIO

import OpenGL
OpenGL.FORWARD_COMPATIBLE_ONLY = True
from OpenGL.GL import *
from OpenGL.GLU import *


class TextureManager(object):
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

        image_file = self.loader.get_file(os.path.basename(first_name))
        textureSurface = pygame.image.load(image_file).convert_alpha()

        if secondary_name:
            alpha_image_file = self.loader.get_file(os.path.basename(secondary_name))
            alphaSurface = pygame.image.load(alpha_image_file)
            assert textureSurface.get_size() == alphaSurface.get_size()
            for x in range(alphaSurface.get_width()):
                for y in range(alphaSurface.get_height()):
                    r, g, b, a = textureSurface.get_at((x, y))
                    color2 = alphaSurface.get_at((x, y))
                    textureSurface.set_at((x, y), (r, g, b, color2[0]))

        textureData = pygame.image.tostring(textureSurface, 'RGBA', 1)

        width = textureSurface.get_width()
        height = textureSurface.get_height()

        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA,
            GL_UNSIGNED_BYTE, textureData)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        return texture

