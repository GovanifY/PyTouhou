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
          GL_UNSIGNED_SHORT_5_6_5, GL_UNSIGNED_SHORT_4_4_4_4_REV, GL_UNSIGNED_SHORT_4_4_4_4,
          glGenTextures, glBindTexture, glTexImage2D, GL_TEXTURE_2D, GLuint,
          glPushDebugGroup, GL_DEBUG_SOURCE_APPLICATION, glPopDebugGroup)

from pytouhou.lib.sdl cimport load_png, create_rgb_surface
from pytouhou.lib.sdl import SDLError
from pytouhou.formats.thtx import Texture #TODO: perhaps define that elsewhere?
from pytouhou.game.text cimport NativeText

from .backend cimport use_debug_group

import os

from pytouhou.utils.helpers import get_logger
logger = get_logger(__name__)


cdef class TextureManager:
    def __init__(self, loader=None, renderer=None, texture_class=None):
        self.loader = loader
        self.renderer = renderer
        self.texture_class = texture_class


    cdef bint load(self, dict anms) except True:
        if use_debug_group:
            glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "Texture loading")

        for anm in sorted(anms.values(), key=is_ascii):
            if use_debug_group:
                glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "Loading textures from ANM")

            for entry in anm:
                if entry.texture is None:
                    texture = decode_png(self.loader, entry.first_name, entry.secondary_name)
                elif not isinstance(entry.texture, self.texture_class):
                    texture = entry.texture
                entry.texture = self.texture_class(load_texture(texture), self.renderer)

            if use_debug_group:
                glPopDebugGroup()
        anms.clear()

        if use_debug_group:
            glPopDebugGroup()


def is_ascii(anm):
    return anm[0].first_name.endswith('ascii.png')


cdef class FontManager:
    def __init__(self, fontname, fontsize=16, renderer=None, texture_class=None):
        self.font = Font(fontname, fontsize)
        self.renderer = renderer
        self.texture_class = texture_class


    cdef bint load(self, dict labels) except True:
        cdef NativeText label

        if use_debug_group:
            glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "Text rendering")

        for i, label in labels.items():
            if label.texture is None:
                try:
                    surface = self.font.render(label.text)
                except SDLError as e:
                    logger.error(u'Rendering of label “%s” failed: %s', label.text, e)
                    del labels[i]  # Prevents it from retrying to render.
                    continue

                label.width, label.height = surface.surface.w, surface.surface.h

                if label.align == 'center':
                    label.x -= label.width // 2
                elif label.align == 'right':
                    label.x -= label.width
                else:
                    assert label.align == 'left'

                texture = Texture(label.width, label.height, -4, surface.pixels)
                label.texture = self.texture_class(load_texture(texture), self.renderer)

        if use_debug_group:
            glPopDebugGroup()


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


cdef GLuint load_texture(thtx) except? 65535:
    cdef GLuint texture
    cdef long fmt = thtx.fmt

    if fmt == 1:
        #format_ = GL_BGRA
        format_ = GL_RGBA #XXX: should be GL_BGRA
        type_ = GL_UNSIGNED_BYTE
        composants = GL_RGBA
    elif fmt == 3:
        format_ = GL_RGB
        type_ = GL_UNSIGNED_SHORT_5_6_5
        composants = GL_RGB
    elif fmt == 5:
        #format_ = GL_BGRA
        format_ = GL_RGBA #XXX: should be GL_BGRA
        #type_ = GL_UNSIGNED_SHORT_4_4_4_4_REV
        type_ = GL_UNSIGNED_SHORT_4_4_4_4 #XXX: should be GL_UNSIGNED_SHORT_4_4_4_4_REV
        composants = GL_RGBA
    elif fmt == 7:
        format_ = GL_LUMINANCE
        type_ = GL_UNSIGNED_BYTE
        composants = GL_LUMINANCE
    elif fmt == -4: #XXX: non-standard
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

    return texture
