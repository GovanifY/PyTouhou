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

from pytouhou.utils.bitstream import BitStream
import pytouhou.utils.lzss as lzss

from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)


class PBG3BitStream(BitStream):
    def read_int(self):
        size = self.read(2)
        return self.read((size + 1) * 8)


    def read_string(self, maxsize):
        string = []
        for i in range(maxsize):
            byte = self.read(8)
            if byte == 0:
                break
            string.append(byte)
        return ''.join(chr(byte) for byte in string)



class PBG3(object):
    def __init__(self, entries, bitstream=None):
        self.entries = entries
        self.bitstream = bitstream #TODO


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        return self.bitstream.__exit__(type, value, traceback)


    @classmethod
    def read(cls, file):
        magic = file.read(4)
        if magic != b'PBG3':
            raise Exception #TODO

        bitstream = PBG3BitStream(file)
        entries = {}

        nb_entries = bitstream.read_int()
        offset = bitstream.read_int()
        bitstream.seek(offset)
        for i in range(nb_entries):
            unknown1 = bitstream.read_int()
            unknown2 = bitstream.read_int()
            checksum = bitstream.read_int() # Checksum of *compressed data*
            offset = bitstream.read_int()
            size = bitstream.read_int()
            name = bitstream.read_string(255).decode('ascii')
            entries[name] = (unknown1, unknown2, checksum, offset, size)

        return PBG3(entries, bitstream)


    def list_files(self):
        return self.entries.keys()


    def extract(self, filename, check=False):
        unkwn1, unkwn2, checksum, offset, size = self.entries[filename]
        self.bitstream.seek(offset)
        data = lzss.decompress(self.bitstream, size)
        if check:
            # Checking the checksum
            compressed_size = self.bitstream.io.tell() - offset
            self.bitstream.seek(offset)
            value = 0
            for c in self.bitstream.io.read(compressed_size):
                value += ord(c)
                value &= 0xFFFFFFFF
            if value != checksum:
                logger.warn('corrupted data!')
        return data

