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

class BitStream(object):
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


    def read_bit(self):
        if not self.bits:
            self.byte = ord(self.io.read(1))
            self.bits = 8
        self.bits -= 1
        return (self.byte >> self.bits) & 0x01


    def read(self, nb_bits):
        value = 0
        for i in range(nb_bits - 1, -1, -1):
            value |= self.read_bit() << i
        return value


    def write_bit(self, bit):
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

