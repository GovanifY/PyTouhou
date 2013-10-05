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

from libc.math cimport sin, cos
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy


cdef float[16] identity
identity[:] = [1, 0, 0, 0,
               0, 1, 0, 0,
               0, 0, 1, 0,
               0, 0, 0, 1]


cdef class Matrix:
    def __init__(self, data=None):
        if data is not None:
            for i in xrange(16):
                self.data[i] = data[i]
        else:
            memcpy(self.data, identity, 16 * sizeof(float))


    def __mul__(Matrix self, Matrix other):
        cdef float *d1, *d2, *d3

        out = Matrix()
        d1 = self.data
        d2 = other.data
        d3 = out.data
        for i in xrange(4):
            for j in xrange(4):
                d3[4*i+j] = 0
                for k in xrange(4):
                    d3[4*i+j] += d1[4*i+k] * d2[4*k+j]
        return out


    cdef void flip(self) nogil:
        cdef float *data

        data = self.data
        for i in xrange(4):
            data[i] = -data[i]


    cdef void scale(self, float x, float y, float z) nogil:
        cdef float *data, coordinate[3]

        data = self.data
        coordinate[0] = x
        coordinate[1] = y
        coordinate[2] = z

        for i in xrange(3):
            for j in xrange(4):
                data[4*i+j] *= coordinate[i]


    cdef void scale2d(self, float x, float y) nogil:
        cdef float *data

        data = self.data
        for i in xrange(4):
            data[  i] *= x
            data[4+i] *= y


    cdef void translate(self, float x, float y, float z) nogil:
        cdef float *data, coordinate[3], item[3]

        data = self.data
        coordinate[0] = x
        coordinate[1] = y
        coordinate[2] = z
        for i in xrange(3):
            item[i] = data[12+i] * coordinate[i]

        for i in xrange(3):
            for j in xrange(4):
                data[4*i+j] += item[i]


    cdef void rotate_x(self, float angle) nogil:
        cdef float cos_a, sin_a
        cdef float lines[8], *data

        data = self.data
        cos_a = cos(angle)
        sin_a = sin(angle)
        for i in xrange(8):
            lines[i] = data[i+4]
        for i in xrange(4):
            data[4+i] = cos_a * lines[i] - sin_a * lines[4+i]
            data[8+i] = sin_a * lines[i] + cos_a * lines[4+i]


    cdef void rotate_y(self, float angle) nogil:
        cdef float cos_a, sin_a
        cdef float lines[8], *data

        data = self.data
        cos_a = cos(angle)
        sin_a = sin(angle)
        for i in xrange(4):
            lines[i] = data[i]
            lines[i+4] = data[i+8]
        for i in xrange(4):
            data[  i] =  cos_a * lines[i] + sin_a * lines[4+i]
            data[8+i] = -sin_a * lines[i] + cos_a * lines[4+i]


    cdef void rotate_z(self, float angle) nogil:
        cdef float cos_a, sin_a
        cdef float lines[8], *data

        data = self.data
        cos_a = cos(angle)
        sin_a = sin(angle)
        for i in xrange(8):
            lines[i] = data[i]
        for i in xrange(4):
            data[  i] = cos_a * lines[i] - sin_a * lines[4+i]
            data[4+i] = sin_a * lines[i] + cos_a * lines[4+i]
