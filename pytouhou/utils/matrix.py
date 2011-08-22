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

#TODO: find/learn to use a proper lib

from math import sin, cos

class Matrix(object):
    def __init__(self, data=None):
        self.data = data or [[0] * 4 for i in xrange(4)]


    def mult(self, other_matrix):
        d1 = self.data
        d2 = other_matrix.data
        return Matrix([[sum(d1[i][a] * d2[a][j] for a in xrange(4)) for j in xrange(4)] for i in xrange(4)])


    def flip(self):
        self.data[0][:] = (-x for x in self.data[0])


    def scale(self, x, y, z):
        d1 = self.data
        d1[0][:] = (a * x for a in d1[0])
        d1[1][:] = (a * y for a in d1[1])
        d1[2][:] = (a * z for a in d1[2])


    def scale2d(self, x, y):
        d1 = self.data
        d1[0][:] = (a * x for a in d1[0])
        d1[1][:] = (a * y for a in d1[1])


    def translate(self, x, y, z):
        d1 = self.data
        a, b, c = (v * m for v, m in zip(d1[3][:3], (x, y, z)))
        d1[0][:] = (v + a for v in d1[0])
        d1[1][:] = (v + b for v in d1[1])
        d1[2][:] = (v + c for v in d1[2])


    def rotate_x(self, angle):
        d1 = self.data
        cos_a = cos(angle)
        sin_a = sin(angle)
        d1[1][:], d1[2][:] = ([cos_a * d1[1][i] - sin_a * d1[2][i] for i in range(4)],
                              [sin_a * d1[1][i] + cos_a * d1[2][i] for i in range(4)])


    def rotate_y(self, angle):
        d1 = self.data
        cos_a = cos(angle)
        sin_a = sin(angle)
        d1[0][:], d1[2][:] = ([cos_a * d1[0][i] + sin_a * d1[2][i] for i in range(4)],
                              [- sin_a * d1[0][i] + cos_a * d1[2][i] for i in range(4)])


    def rotate_z(self, angle):
        d1 = self.data
        cos_a = cos(angle)
        sin_a = sin(angle)
        d1[0][:], d1[1][:] = ([cos_a * d1[0][i] - sin_a * d1[1][i] for i in range(4)],
                              [sin_a * d1[0][i] + cos_a * d1[1][i] for i in range(4)])


    @classmethod
    def get_translation_matrix(cls, x, y, z):
        return cls([[1., 0., 0., x],
                    [0., 1., 0., y],
                    [0., 0., 1., z],
                    [0., 0., 0., 1.]])


    @classmethod
    def get_scaling_matrix(cls, x, y, z):
        return cls([[x,  0., 0., 0.],
                    [0., y,  0., 0.],
                    [0., 0., z,  0.],
                    [0., 0., 0., 1.]])


    @classmethod
    def get_rotation_matrix(cls, angle, axis):
        """Only handles axis = x, y or z."""
        cos_a = cos(angle)
        sin_a = sin(angle)
        if axis == 'x':
            return Matrix([[    1.,     0.,     0.,     0.],
                           [    0.,  cos_a, -sin_a,     0.],
                           [    0.,  sin_a,  cos_a,     0.],
                           [    0.,     0.,     0.,     1.]])
        elif axis == 'y':
            return Matrix([[ cos_a,     0.,  sin_a,     0.],
                           [    0.,     1.,     0.,     0.],
                           [-sin_a,     0.,  cos_a,     0.],
                           [    0.,     0.,     0.,     1.]])
        elif axis == 'z':
            return Matrix([[ cos_a, -sin_a,     0.,     0.],
                           [ sin_a,  cos_a,     0.,     0.],
                           [    0.,     0.,     1.,     0.],
                           [    0.,     0.,     0.,     1.]])
        else:
            raise Exception

