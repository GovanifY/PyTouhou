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


cdef Matrix identity
identity = Matrix(1, 0, 0, 0,
                  0, 1, 0, 0,
                  0, 0, 1, 0,
                  0, 0, 0, 1)


cdef Matrix *new_matrix(Matrix *data) nogil:
    mat = <Matrix*> malloc(sizeof(Matrix))
    memcpy(mat, data, sizeof(Matrix))
    return mat


cdef Matrix *new_identity() nogil:
    return new_matrix(&identity)


cdef void mul(Matrix *mat1, Matrix *mat2) nogil:
    cdef float *d3

    out = <Matrix*> malloc(sizeof(Matrix))
    d1 = <float*>mat1
    d2 = <float*>mat2
    d3 = <float*>out
    for i in xrange(4):
        for j in xrange(4):
            d3[4*i+j] = 0
            for k in xrange(4):
                d3[4*i+j] += d1[4*i+k] * d2[4*k+j]
    memcpy(mat1, out, sizeof(Matrix))
    free(out)


cdef void flip(Matrix *mat) nogil:
    data = <float*>mat
    for i in xrange(4):
        data[i] = -data[i]


cdef void scale(Matrix *mat, float x, float y, float z) nogil:
    cdef float coordinate[3]

    data = <float*>mat
    coordinate[0] = x
    coordinate[1] = y
    coordinate[2] = z

    for i in xrange(3):
        for j in xrange(4):
            data[4*i+j] *= coordinate[i]


cdef void scale2d(Matrix *mat, float x, float y) nogil:
    data = <float*>mat
    for i in xrange(4):
        data[  i] *= x
        data[4+i] *= y


cdef void translate(Matrix *mat, float x, float y, float z) nogil:
    cdef float offset[3], item[3]

    offset[0] = x
    offset[1] = y
    offset[2] = z

    data = <float*>mat
    for i in xrange(3):
        item[i] = data[12+i] * offset[i]

    for i in xrange(3):
        for j in xrange(4):
            data[4*i+j] += item[i]


cdef void translate2d(Matrix *mat, float x, float y) nogil:
    translate(mat, x, y, 0)


cdef void rotate_x(Matrix *mat, float angle) nogil:
    cdef float cos_a, sin_a
    cdef float lines[8]

    data = <float*>mat
    cos_a = cos(angle)
    sin_a = sin(angle)
    for i in xrange(8):
        lines[i] = data[i+4]
    for i in xrange(4):
        data[4+i] = cos_a * lines[i] - sin_a * lines[4+i]
        data[8+i] = sin_a * lines[i] + cos_a * lines[4+i]


cdef void rotate_y(Matrix *mat, float angle) nogil:
    cdef float cos_a, sin_a
    cdef float lines[8]

    data = <float*>mat
    cos_a = cos(angle)
    sin_a = sin(angle)
    for i in xrange(4):
        lines[i] = data[i]
        lines[i+4] = data[i+8]
    for i in xrange(4):
        data[  i] =  cos_a * lines[i] + sin_a * lines[4+i]
        data[8+i] = -sin_a * lines[i] + cos_a * lines[4+i]


cdef void rotate_z(Matrix *mat, float angle) nogil:
    cdef float cos_a, sin_a
    cdef float lines[8]

    data = <float*>mat
    cos_a = cos(angle)
    sin_a = sin(angle)
    for i in xrange(8):
        lines[i] = data[i]
    for i in xrange(4):
        data[  i] = cos_a * lines[i] - sin_a * lines[4+i]
        data[4+i] = sin_a * lines[i] + cos_a * lines[4+i]
