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

from pytouhou.lib.sdl cimport load_png, create_rgb_surface
from pytouhou.lib.sdl import SDLError
from pytouhou.game.text cimport NativeText

import os

from pytouhou.utils.helpers import get_logger
logger = get_logger(__name__)


cdef class TextureManager:
    def __init__(self, loader, window):
        self.loader = loader
        self.window = window


    cdef bint load(self, dict anms) except True:
        for anm in sorted(anms.values(), key=is_ascii):
            for entry in anm:
                if entry.texture is None:
                    texture = decode_png(self.loader, entry.first_name, entry.secondary_name)
                #elif not isinstance(entry.texture, self.texture_class):
                #    texture = entry.texture
                entry.texture = self.load_texture(texture)
        anms.clear()


    cdef load_texture(self, Surface surface):
        return self.window.create_texture_from_surface(surface)


def is_ascii(anm):
    return anm[0].first_name.endswith('ascii.png')


cdef class FontManager:
    def __init__(self, fontname, fontsize=16, window=None):
        self.font = Font(fontname, fontsize)
        self.window = window


    cdef bint load(self, dict labels) except True:
        cdef NativeText label

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

                label.texture = self.window.create_texture_from_surface(surface)


cdef Surface decode_png(loader, first_name, secondary_name):
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

    return new_image
