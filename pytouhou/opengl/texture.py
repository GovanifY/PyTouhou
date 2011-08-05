import pygame
import os
from io import BytesIO

import OpenGL
OpenGL.FORWARD_COMPATIBLE_ONLY = True
from OpenGL.GL import *
from OpenGL.GLU import *


def load_texture(archive, anim):
    image_file = BytesIO(archive.extract(os.path.basename(anim.first_name)))
    textureSurface = pygame.image.load(image_file).convert_alpha()

    if anim.secondary_name:
        alpha_image_file = BytesIO(archive.extract(os.path.basename(anim.secondary_name)))
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

    return texture, width, height

