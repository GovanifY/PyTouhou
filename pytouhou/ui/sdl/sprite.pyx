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

cimport cython
from libc.stdlib cimport malloc
from libc.math cimport M_PI as pi


cdef RenderingData* get_sprite_rendering_data(Sprite sprite) nogil:
    if sprite.changed:
        render_sprite(sprite)
    return <RenderingData*>sprite._rendering_data


@cython.cdivision(True)
cdef void render_sprite(Sprite sprite) nogil:
    if sprite._rendering_data == NULL:
        sprite._rendering_data = malloc(sizeof(RenderingData))

    data = <RenderingData*>sprite._rendering_data

    x = 0
    y = 0

    tx, ty, tw, th = sprite._texcoords[0], sprite._texcoords[1], sprite._texcoords[2], sprite._texcoords[3]
    sx, sy = sprite._rescale[0], sprite._rescale[1]
    width = sprite.width_override or (tw * sx)
    height = sprite.height_override or (th * sy)

    rz = sprite._rotations_3d[2]
    if sprite.automatic_orientation:
        rz += pi/2. - sprite.angle
    elif sprite.force_rotation:
        rz += sprite.angle

    if sprite.allow_dest_offset:
        x += sprite._dest_offset[0]
        y += sprite._dest_offset[1]
    if not sprite.corner_relative_placement: # Reposition
        x -= width / 2
        y -= height / 2

    data.x = <int>x
    data.y = <int>y
    data.width = <int>width
    data.height = <int>height

    x_1 = sprite.anm.size_inv[0]
    y_1 = sprite.anm.size_inv[1]
    tox, toy = sprite._texoffsets[0], sprite._texoffsets[1]
    data.left = tx * x_1 + tox
    data.right = (tx + tw) * x_1 + tox
    data.bottom = ty * y_1 + toy
    data.top = (ty + th) * y_1 + toy

    data.r, data.g, data.b, data.a = sprite._color[0], sprite._color[1], sprite._color[2], sprite._color[3]

    data.blendfunc = sprite.blendfunc
    data.rotation = -rz * 180 / pi
    data.flip = sprite.mirrored

    sprite.changed = False
