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


"""
This file provides a pseudo-random number generator identical to the one used in
Touhou 6: The Embodiment of Scarlet Devil.
It is the only truly reverse-engineered piece of code of this project,
as it is needed in order to retain compatibility with replay files produced by
the offical game code.

It has been reverse engineered from 102h.exe."""


#TODO: maybe some post-processing is missing

cimport cython
from time import time


@cython.final
cdef class Random:
    def __init__(self, long seed=-1):
        if seed < 0:
            seed = time()
        self.set_seed(<unsigned short>(seed & 65535))


    cdef void set_seed(self, unsigned short seed) nogil:
        self.seed = seed
        self.counter = 0


    cdef unsigned short rewind(self) nogil:
        """Rewind the PRNG by 1 step. This is the reverse of rand_uint16.
        Might be useful for debugging purposes.
        """
        x = self.seed
        x = (x >> 2) | ((x & 3) << 14)
        self.seed = ((x + 0x6553) & 0xffff) ^ 0x9630
        self.counter -= 1
        return self.seed


    cpdef unsigned short rand_uint16(self):
        # 102h.exe@0x41e780
        x = ((self.seed ^ 0x9630) - 0x6553) & 0xffff
        self.seed = (((x & 0xc000) >> 14) | (x << 2)) & 0xffff
        self.counter += 1
        return self.seed


    cpdef unsigned int rand_uint32(self):
        # 102h.exe@0x41e7f0
        a = self.rand_uint16() << 16
        a |= self.rand_uint16()
        return a


    cpdef double rand_double(self):
        # 102h.exe@0x41e820
        return self.rand_uint32() / <double>0x100000000
