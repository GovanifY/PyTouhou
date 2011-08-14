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
        self.seed = (((x & 0x0c000) >> 0xe) + x*4) & 0xffff
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

