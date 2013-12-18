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

from libc.math cimport tan, M_PI as pi
cimport cython

from .matrix cimport new_matrix, new_identity
from .vector cimport Vector, sub, cross, dot, normalize


cdef double radians(double degrees) nogil:
    return degrees * pi / 180


@cython.cdivision(True)
cdef Matrix *ortho_2d(float left, float right, float bottom, float top) nogil:
    mat = new_identity()
    data = <float*>mat
    data[4*0+0] = 2 / (right - left)
    data[4*1+1] = 2 / (top - bottom)
    data[4*2+2] = -1
    data[4*3+0] = -(right + left) / (right - left)
    data[4*3+1] = -(top + bottom) / (top - bottom)
    return mat


cdef Matrix *look_at(Vector eye, Vector center, Vector up):
    cdef Matrix mat

    f = normalize(sub(center, eye))
    u = normalize(up)
    s = normalize(cross(f, u))
    u = cross(s, f)

    mat = Matrix(s.x, u.x, -f.x, 0,
                 s.y, u.y, -f.y, 0,
                 s.z, u.z, -f.z, 0,
                 -dot(s, eye), -dot(u, eye), dot(f, eye), 1)

    return new_matrix(&mat)


@cython.cdivision(True)
cdef Matrix *perspective(float fovy, float aspect, float z_near, float z_far) nogil:
    top = tan(radians(fovy / 2)) * z_near
    bottom = -top
    left = -top * aspect
    right = top * aspect

    mat = new_identity()
    data = <float*>mat
    data[4*0+0] = (2 * z_near) / (right - left)
    data[4*1+1] = (2 * z_near) / (top - bottom)
    data[4*2+2] = -(z_far + z_near) / (z_far - z_near)
    data[4*2+3] = -1
    data[4*3+2] = -(2 * z_far * z_near) / (z_far - z_near)
    data[4*3+3] = 0
    return mat


cdef Matrix *setup_camera(float dx, float dy, float dz):
    # Some explanations on the magic constants:
    # 192. = 384. / 2. = width / 2.
    # 224. = 448. / 2. = height / 2.
    # 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
    # This is so that objects on the (O, x, y) plane use pixel coordinates
    return look_at(Vector(192., 224., - 835.979370 * dz),
                   Vector(192. + dx, 224. - dy, 0.), Vector(0., -1., 0.))
