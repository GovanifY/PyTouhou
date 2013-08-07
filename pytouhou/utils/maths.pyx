# -*- encoding: utf-8 -*-
##
## Copyright (C) 2013 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from math import radians
from libc.math cimport tan

from .matrix cimport Matrix
from .vector import Vector, normalize, cross, dot


cpdef ortho_2d(left, right, bottom, top):
    cdef float *data

    mat = Matrix()
    data = mat.data
    data[4*0+0] = 2 / (right - left)
    data[4*1+1] = 2 / (top - bottom)
    data[4*2+2] = -1
    data[4*3+0] = -(right + left) / (right - left)
    data[4*3+1] = -(top + bottom) / (top - bottom)
    return mat


cpdef look_at(eye, center, up):
    eye = Vector(eye)
    center = Vector(center)
    up = Vector(up)

    f = normalize(center - eye)
    u = normalize(up)
    s = normalize(cross(f, u))
    u = cross(s, f)

    return Matrix([s[0], u[0], -f[0], 0,
                   s[1], u[1], -f[1], 0,
                   s[2], u[2], -f[2], 0,
                   -dot(s, eye), -dot(u, eye), dot(f, eye), 1])


cpdef perspective(fovy, aspect, z_near, z_far):
    cdef float *data

    top = tan(radians(fovy / 2)) * z_near
    bottom = -top
    left = -top * aspect
    right = top * aspect

    mat = Matrix()
    data = mat.data
    data[4*0+0] = (2 * z_near) / (right - left)
    data[4*1+1] = (2 * z_near) / (top - bottom)
    data[4*2+2] = -(z_far + z_near) / (z_far - z_near)
    data[4*2+3] = -1
    data[4*3+2] = -(2 * z_far * z_near) / (z_far - z_near)
    data[4*3+3] = 0
    return mat


cpdef setup_camera(dx, dy, dz):
    # Some explanations on the magic constants:
    # 192. = 384. / 2. = width / 2.
    # 224. = 448. / 2. = height / 2.
    # 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
    # This is so that objects on the (O, x, y) plane use pixel coordinates
    return look_at((192., 224., - 835.979370 * dz),
                   (192. + dx, 224. - dy, 0.), (0., -1., 0.))
