# -*- encoding: utf-8 -*-
##
## Copyright (C) 2012 Thibaut Girka <thib@sitedethib.com>
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


from struct import pack, unpack, Struct
from collections import namedtuple
from io import BytesIO

from pytouhou.formats import ChecksumError


class TH6Score:
    entry_types = {
        b'TH6K': (Struct('<I'),
                  namedtuple('TH6K', ('unknown',))),
        b'HSCR': (Struct('<IIBBB8sx'),
                  namedtuple('HSCR', ('unknown', 'score', 'character',
                                      'rank', 'stage', 'name'))),
        b'PSCR': (Struct('<IIBBBx'),
                  namedtuple('PSCR', ('unknown', 'score', 'character',
                                      'rank', 'stage'))),
        b'CLRD': (Struct('<I5B5BBx'),
                  namedtuple('CLRD', ('unknown',
                                      'easy', 'normal', 'hard', 'lunatic',
                                      'extra',
                                      'easy_continue', 'normal_continue',
                                      'hard_continue', 'lunatic_continue',
                                      'extra_continue',
                                      'character'))),
        b'CATK': (Struct('<I I HH I 34s H HH'),
                  namedtuple('CATK', ('unknown', 'unknown2', 'num',
                                      'unknown3', 'padding',
                                      'name', 'padding2',
                                      'seen',
                                      'defeated'))),
    }

    def __init__(self):
        self.key1 = 0
        self.key2 = 0
        self.unknown1 = 0
        self.unknown2 = 16
        self.unknown3 = 0
        self.unknown4 = 0
        self.entries = []


    @classmethod
    def read(cls, file, decrypt=True, verify=True):
        self = cls()

        # Decrypt data
        if decrypt:
            decrypted_file = BytesIO()
            decrypted_file.write(file.read(1))
            key = 0
            for c in file.read():
                encrypted = ord(c)
                key = ((key << 3) & 0xFF) | ((key >> 5) & 7)
                clear = encrypted ^ key
                key += clear
                decrypted_file.write(chr(clear))
            file = decrypted_file

        # Read first-part header
        file.seek(0)
        self.unknown1, self.key1, checksum = unpack('<BBH', file.read(4))

        # Verify checksum
        if verify:
            #TODO: is there more to it?
            real_sum = sum(ord(c) for c in file.read()) & 0xFFFF
            if checksum != real_sum:
                raise ChecksumError(checksum, real_sum)
            file.seek(4)

        # Read second-part header
        data = unpack('<HBBIII', file.read(16))
        self.unknown2, self.key2, self.unknown3, offset, self.unknown4, size = data

        #TODO: verify size

        # Read tags
        file.seek(offset)
        while True:
            tag = file.read(4)
            if not tag:
                break
            size, size2 = unpack('<HH', file.read(4))
            assert size == size2
            assert size >= 8
            data = file.read(size-8)
            data = cls.entry_types[tag][0].unpack(data)
            data = cls.entry_types[tag][1](*data)
            self.entries.append((tag, data))

        return self


    def write(self, file, encrypt=True):
        if encrypt:
            clearfile = BytesIO()
        else:
            clearfile = file

        # Write data
        clearfile.seek(20)
        for entry in self.entries:
            #TODO
            tag, data = entry
            format = TH6Score.entry_types[tag][0]
            clearfile.write(tag)
            clearfile.write(pack('<H', format.size + 8) * 2)
            clearfile.write(format.pack(*data))

        # Patch header
        size = clearfile.tell()
        clearfile.seek(0)
        clearfile.write(pack('<BBHHBBIII',
                             self.unknown1, self.key1, 0, self.unknown2,
                             self.key2, self.unknown3, 20, self.unknown4,
                             size))

        # Patch checksum
        clearfile.seek(4)
        checksum = sum(ord(c) for c in clearfile.read()) & 0xFFFF
        clearfile.seek(2)
        clearfile.write(pack('<H', checksum))

        # Encrypt
        if encrypt:
            clearfile.seek(0)
            file.write(clearfile.read(1))
            key = 0
            for c in clearfile.read():
                clear = ord(c)
                key = ((key << 3) & 0xFF) | ((key >> 5) & 7)
                encrypted = clear ^ key
                key += clear
                file.write(chr(encrypted))

