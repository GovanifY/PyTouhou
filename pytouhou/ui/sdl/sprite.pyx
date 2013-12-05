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


from libc.math cimport M_PI as pi


cpdef tuple get_sprite_rendering_data(Sprite sprite):
    cdef double x, y, tx, ty, tw, th, sx, sy, rz, tox, toy

    if not sprite.changed:
        return sprite._rendering_data

    x = 0
    y = 0

    tx, ty, tw, th = sprite.texcoords
    sx, sy = sprite.rescale
    width = sprite.width_override or (tw * sx)
    height = sprite.height_override or (th * sy)

    rz = sprite.rotations_3d[2]
    if sprite.automatic_orientation:
        rz += pi/2. - sprite.angle
    elif sprite.force_rotation:
        rz += sprite.angle

    if sprite.allow_dest_offset:
        x += sprite.dest_offset[0]
        y += sprite.dest_offset[1]
    if not sprite.corner_relative_placement: # Reposition
        x -= width / 2
        y -= height / 2

    size = sprite.anm.size
    x_1 = 1 / <double>size[0]
    y_1 = 1 / <double>size[1]
    tox, toy = sprite.texoffsets
    uvs = (tx * x_1 + tox,
           (tx + tw) * x_1 + tox,
           ty * y_1 + toy,
           (ty + th) * y_1 + toy)

    key = sprite.blendfunc
    r, g, b = sprite.color
    values = (x, y, width, height), uvs, (r, g, b, sprite.alpha), -rz * 180 / pi, sprite.mirrored
    sprite._rendering_data = key, values
    sprite.changed = False

    return sprite._rendering_data
