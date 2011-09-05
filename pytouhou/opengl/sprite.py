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


from math import pi

from pytouhou.utils.matrix import Matrix


def get_sprite_rendering_data(sprite):
    if not sprite._changed:
        return sprite._rendering_data

    if sprite.fade_interpolator:
        sprite.fade_interpolator.update(sprite.frame)
        sprite.alpha = int(sprite.fade_interpolator.values[0])

    if sprite.scale_interpolator:
        sprite.scale_interpolator.update(sprite.frame)
        sprite.rescale = sprite.scale_interpolator.values

    if sprite.offset_interpolator:
        sprite.offset_interpolator.update(sprite.frame)
        sprite.dest_offset = sprite.offset_interpolator.values

    vertmat = Matrix([[-.5,     .5,     .5,    -.5],
                      [-.5,    -.5,     .5,     .5],
                      [ .0,     .0,     .0,     .0],
                      [ 1.,     1.,     1.,     1.]])

    tx, ty, tw, th = sprite.texcoords
    sx, sy = sprite.rescale
    width = sprite.width_override or (tw * sx)
    height = sprite.height_override or (th * sy)

    vertmat.scale2d(width, height)
    if sprite.mirrored:
        vertmat.flip()

    rx, ry, rz = sprite.rotations_3d
    if sprite.automatic_orientation:
        rz += pi/2. - sprite.angle
    elif sprite.force_rotation:
        rz += sprite.angle

    if (rx, ry, rz) != (0., 0., 0.):
        if rx:
            vertmat.rotate_x(-rx)
        if ry:
            vertmat.rotate_y(ry)
        if rz:
            vertmat.rotate_z(-rz) #TODO: minus, really?
    if sprite.corner_relative_placement: # Reposition
        vertmat.translate(width / 2., height / 2., 0.)
    if sprite.allow_dest_offset:
        vertmat.translate(*sprite.dest_offset)

    x_1 = 1. / sprite.anm.size[0]
    y_1 = 1. / sprite.anm.size[1]
    tox, toy = sprite.texoffsets
    uvs = [(tx * x_1 + tox,         1. - (ty * y_1) + toy),
           ((tx + tw) * x_1 + tox,  1. - (ty * y_1) + toy),
           ((tx + tw) * x_1 + tox,  1. - ((ty + th) * y_1 + toy)),
           (tx * x_1 + tox,         1. - ((ty + th) * y_1 + toy))]

    d = vertmat.data
    assert (d[3][0], d[3][1], d[3][2], d[3][3]) == (1., 1., 1., 1.)

    key = (sprite.anm.first_name, sprite.anm.secondary_name), sprite.blendfunc
    values = zip(d[0], d[1], d[2]), uvs, [(sprite.color[0], sprite.color[1], sprite.color[2], sprite.alpha)] * 4
    sprite._rendering_data = key, values
    sprite._changed = False

    return sprite._rendering_data

