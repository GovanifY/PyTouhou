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

from math import sqrt


class Vector(list):
    def __init__(self, data=None):
        list.__init__(self, data or [0] * 3)


    def __add__(self, other):
        return Vector([a+b for a, b in zip(self, other)])


    def __sub__(self, other):
        return Vector([a-b for a, b in zip(self, other)])


def cross(vec1, vec2):
    return Vector([vec1[1] * vec2[2] - vec2[1] * vec1[2],
                   vec1[2] * vec2[0] - vec2[2] * vec1[0],
                   vec1[0] * vec2[1] - vec2[0] * vec1[1]])


def dot(vec1, vec2):
    return vec1[0] * vec2[0] + vec2[1] * vec1[1] + vec1[2] * vec2[2]


def normalize(vec1):
    normal = 1 / sqrt(vec1[0] * vec1[0] + vec1[1] * vec1[1] + vec1[2] * vec1[2])
    return Vector(x * normal for x in vec1)
