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

from pytouhou.utils.matrix cimport Matrix


cpdef object get_sprite_rendering_data(Sprite sprite):
    cdef Matrix vertmat
    cdef double tx, ty, tw, th, sx, sy, rx, ry, rz, tox, toy
    cdef object tmp1, tmp2

    if not sprite.changed:
        return sprite._rendering_data

    tmp1 = .5
    tmp2 = -.5
    vertmat = Matrix([tmp2, tmp1, tmp1, tmp2,
                      tmp2, tmp2, tmp1, tmp1,
                      0,    0,    0,    0,
                      1,    1,    1,    1])

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

    if rx:
        vertmat.rotate_x(-rx)
    if ry:
        vertmat.rotate_y(ry)
    if rz:
        vertmat.rotate_z(-rz) #TODO: minus, really?
    if sprite.allow_dest_offset:
        vertmat.translate(sprite.dest_offset[0], sprite.dest_offset[1], sprite.dest_offset[2])
    if sprite.corner_relative_placement: # Reposition
        vertmat.translate(width / 2, height / 2, 0)

    x_1 = 1 / <double>sprite.anm.size[0]
    y_1 = 1 / <double>sprite.anm.size[1]
    tox, toy = sprite.texoffsets
    uvs = (tx * x_1 + tox,
           (tx + tw) * x_1 + tox,
           ty * y_1 + toy,
           (ty + th) * y_1 + toy)

    key = MAX_TEXTURES * sprite.blendfunc + <long>sprite.anm.texture
    r, g, b = sprite.color
    values = tuple([x for x in vertmat.data[:12]]), uvs, (r, g, b, sprite.alpha)
    sprite._rendering_data = key, values
    sprite.changed = False

    return sprite._rendering_data
