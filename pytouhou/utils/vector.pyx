# -*- encoding: utf-8 -*-
##
## Copyright (C) 2012 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from libc.math cimport sqrt
cimport cython


cdef Vector sub(Vector vec1, Vector vec2):
    return Vector(vec1.x - vec2.x,
                  vec1.y - vec2.y,
                  vec1.z - vec2.z)


cdef Vector cross(Vector vec1, Vector vec2):
    return Vector(vec1.y * vec2.z - vec2.y * vec1.z,
                  vec1.z * vec2.x - vec2.z * vec1.x,
                  vec1.x * vec2.y - vec2.x * vec1.y)


cdef float dot(Vector vec1, Vector vec2) nogil:
    return vec1.x * vec2.x + vec2.y * vec1.y + vec1.z * vec2.z


@cython.cdivision(True)
cdef Vector normalize(Vector vec):
    cdef float normal

    normal = 1 / sqrt(vec.x * vec.x + vec.y * vec.y + vec.z * vec.z)
    return Vector(vec.x * normal, vec.y * normal, vec.z * normal)
