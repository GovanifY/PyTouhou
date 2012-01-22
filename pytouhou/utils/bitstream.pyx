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

cdef class BitStream:
    cdef public io
    cdef public int bits
    cdef public unsigned char byte


    def __init__(BitStream self, io):
        self.io = io
        self.bits = 0
        self.byte = 0


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        return self.io.__exit__(type, value, traceback)


    def seek(BitStream self, offset, whence=0):
        self.io.seek(offset, whence)
        self.byte = 0
        self.bits = 0


    def tell(BitStream self):
        return self.io.tell()


    def tell2(BitStream self):
        return self.io.tell(), self.bits


    cpdef unsigned char read_bit(BitStream self):
        if not self.bits:
            self.byte = ord(self.io.read(1))
            self.bits = 8
        self.bits -= 1
        return (self.byte >> self.bits) & 0x01


    cpdef unsigned int read(BitStream self, int nb_bits):
        cdef unsigned int value = 0
        cdef int i

        for i in range(nb_bits - 1, -1, -1):
            value |= self.read_bit() << i
        return value


    cpdef write_bit(BitStream self, bit):
        if self.bits == 8:
            self.io.write(chr(self.byte))
            self.bits = 0
            self.byte = 0
        self.byte &= ~(1 << (7 - self.bits))
        self.byte |= bit << (7 - self.bits)
        self.bits += 1


    def write(BitStream self, bits, nb_bits):
        for i in range(nb_bits):
            self.write_bit(bits >> (nb_bits - 1 - i) & 0x01)


    def flush(BitStream self):
        self.io.write(chr(self.byte))
        self.bits = 0
        self.byte = 0
        self.io.flush()

