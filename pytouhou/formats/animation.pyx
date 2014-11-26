# -*- encoding: utf-8 -*-
##
## Copyright (C) 2014 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

cdef class Animation:
    def __init__(self):
        self.version = 0
        self.size_inv[:] = [0, 0]
        self.first_name = None
        self.secondary_name = None
        self.sprites = {}
        self.scripts = {}

    property size:
        def __set__(self, tuple value):
            width, height = value
            self.size_inv[:] = [1. / <double>width, 1. / <double>height]
