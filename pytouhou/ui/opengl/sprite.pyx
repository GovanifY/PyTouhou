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


from libc.stdlib cimport malloc
from libc.string cimport memcpy
from libc.math cimport M_PI as pi

from pytouhou.utils.matrix cimport Matrix, scale2d, flip, rotate_x, rotate_y, rotate_z, translate, translate2d
from .renderer cimport Texture #XXX


cdef Matrix default
default = Matrix(-.5,   .5,   .5,  -.5,
                 -.5,  -.5,   .5,   .5,
                 0,    0,    0,    0,
                 1,    1,    1,    1)


cdef RenderingData* get_sprite_rendering_data(Sprite sprite) nogil:
    if sprite.changed:
        render_sprite(sprite)
    return <RenderingData*>sprite._rendering_data


def get_sprite_vertices(Sprite sprite):
    if sprite.changed:
        render_sprite(sprite)
    data = <RenderingData*>sprite._rendering_data
    return [(data.pos[0], data.pos[1], data.pos[2]),
            (data.pos[3], data.pos[4], data.pos[5]),
            (data.pos[6], data.pos[7], data.pos[8]),
            (data.pos[9], data.pos[10], data.pos[11])]


cdef void render_sprite(Sprite sprite) nogil:
    cdef Matrix vertmat

    if sprite._rendering_data == NULL:
        sprite._rendering_data = malloc(sizeof(RenderingData))

    data = <RenderingData*>sprite._rendering_data
    memcpy(&vertmat, &default, sizeof(Matrix))

    tx, ty, tw, th = sprite._texcoords[0], sprite._texcoords[1], sprite._texcoords[2], sprite._texcoords[3]
    sx, sy = sprite._rescale[0], sprite._rescale[1]
    width = sprite.width_override or (tw * sx)
    height = sprite.height_override or (th * sy)

    scale2d(&vertmat, width, height)
    if sprite.mirrored:
        flip(&vertmat)

    rx, ry, rz = sprite._rotations_3d[0], sprite._rotations_3d[1], sprite._rotations_3d[2]
    if sprite.automatic_orientation:
        rz += pi/2. - sprite.angle
    elif sprite.force_rotation:
        rz += sprite.angle

    if rx:
        rotate_x(&vertmat, -rx)
    if ry:
        rotate_y(&vertmat, ry)
    if rz:
        rotate_z(&vertmat, -rz) #TODO: minus, really?
    if sprite.allow_dest_offset:
        translate(&vertmat, sprite._dest_offset)
    if sprite.corner_relative_placement: # Reposition
        translate2d(&vertmat, width / 2, height / 2)

    memcpy(data.pos, &vertmat, 12 * sizeof(float))

    x_1 = sprite.anm.size_inv[0]
    y_1 = sprite.anm.size_inv[1]
    tox, toy = sprite._texoffsets[0], sprite._texoffsets[1]
    data.left = tx * x_1 + tox
    data.right = (tx + tw) * x_1 + tox
    data.bottom = ty * y_1 + toy
    data.top = (ty + th) * y_1 + toy

    for i in range(4):
        data.color[i] = sprite._color[i]

    data.key = ((<Texture>sprite.anm.texture).key << 1) | sprite.blendfunc
    sprite.changed = False
