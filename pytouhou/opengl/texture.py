import pygame
import os
from io import BytesIO

import OpenGL
OpenGL.FORWARD_COMPATIBLE_ONLY = True
from OpenGL.GL import *
from OpenGL.GLU import *


class TextureManager(object):
    def __init__(self, archive):
        self.archive = archive
        self.textures = {}

    def __getitem__(self, key):
        if not key in self.textures:
            self.textures[key] = self.load_texture(key)
        return self.textures[key]


    def set_archive(self, archive):
        self.archive = archive


    def load_texture(self, key):
        first_name, secondary_name = key

        image_file = BytesIO(self.archive.extract(os.path.basename(first_name)))
        textureSurface = pygame.image.load(image_file).convert_alpha()

        if secondary_name:
            alpha_image_file = BytesIO(self.archive.extract(os.path.basename(secondary_name)))
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

