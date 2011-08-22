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

It has been reverse engineered from 102h.exe@0x41e780."""


#TODO: maybe some post-processing is missing


from time import time

class Random(object):
    def __init__(self, seed=None):
        if seed is None:
            seed = int(time() % 65536)
        self.seed = seed
        self.counter = 0


    def set_seed(self, seed):
        self.seed = seed
        self.counter = 0


    def rand_uint16(self):
        # Further reverse engineering might be needed.
        x = ((self.seed ^ 0x9630) - 0x6553) & 0xffff
        self.seed = (((x & 0x0c000) >> 0xe) | (x << 2)) & 0xffff
        self.counter += 1
        self.counter &= 0xffff
        return self.seed


    def rand_uint32(self):
        # 102h.exe@0x41e7f0
        a = self.rand_uint16() << 16
        a |= self.rand_uint16()
        return a


    def rand_double(self):
        # 102h.exe@0x41e820
        return float(self.rand_uint32()) / 0x100000000

