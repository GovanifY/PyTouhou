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
    cdef public object io
    cdef unsigned int bits
    cdef unsigned char byte
    cdef bytes bytes


    def __init__(self, io):
        self.io = io
        self.bits = 0
        self.byte = 0


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        return self.io.__exit__(type, value, traceback)


    def seek(self, offset, whence=0):
        self.io.seek(offset, whence)
        self.byte = 0
        self.bits = 0


    def tell(self):
        return self.io.tell()


    def tell2(self):
        return self.io.tell(), self.bits


    cpdef unsigned char read_bit(self) except? -1:
        if not self.bits:
            self.bytes = self.io.read(1)
            self.byte = (<unsigned char*> self.bytes)[0]
            self.bits = 8
        self.bits -= 1
        return (self.byte >> self.bits) & 0x01


    cpdef unsigned int read(self, unsigned int nb_bits) except? -1:
        cdef unsigned int value = 0, read = 0
        cdef unsigned int nb_bits2 = nb_bits

        while nb_bits2:
            if not self.bits:
                self.bytes = self.io.read(1)
                self.byte = (<unsigned char*> self.bytes)[0]
                self.bits = 8
            read = self.bits if nb_bits2 > self.bits else nb_bits2
            nb_bits2 -= read
            self.bits -= read
            value |= (self.byte >> self.bits) << nb_bits2
        return value & ((1 << nb_bits) - 1)


    cpdef write_bit(self, bit):
        if self.bits == 8:
            self.io.write(chr(self.byte))
            self.bits = 0
            self.byte = 0
        self.byte &= ~(1 << (7 - self.bits))
        self.byte |= bit << (7 - self.bits)
        self.bits += 1


    def write(self, bits, nb_bits):
        for i in range(nb_bits):
            self.write_bit(bits >> (nb_bits - 1 - i) & 0x01)


    def flush(self):
        self.io.write(chr(self.byte))
        self.bits = 0
        self.byte = 0
        self.io.flush()

