# -*- encoding: utf-8 -*-
##
## Copyright (C) 2011 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

"""Touhou 6 Replay (T6RP) files handling.

This module provides classes for handling the Touhou 6 Replay file format.
The T6RP file format is an encrypted format describing different aspects of
a game of EoSD. Since the EoSD engine is entirely deterministic, a small
replay file is sufficient to unfold a full game.
"""

from struct import unpack, pack
from io import BytesIO
from time import strftime

from pytouhou.utils.helpers import read_string, get_logger
from pytouhou.formats import ChecksumError

logger = get_logger(__name__)


class Level:
    def __init__(self):
        self.score = 0
        self.random_seed = 0
        self.point_items = 0

        self.power = 0
        self.lives = 2
        self.bombs = 3
        self.difficulty = 16
        self.unknown = 0
        self.keys = []


    def iter_keystates(self):
        counter = 0
        previous = 0
        for frame, keystate, unknown in self.keys:
            while frame >= counter:
                yield previous
                counter += 1
            previous = keystate



class T6RP:
    def __init__(self):
        self.version = 0x102
        self.character = 0
        self.rank = 0
        self.unknown1 = 0
        self.unknown2 = 0
        self.key = 0
        self.unknown3 = 0
        self.date = strftime('%d/%m/%y')
        self.name = 'PyTouhou'
        self.unknown4 = 0
        self.score = 0
        self.unknown5 = 0
        self.slowdown = 0.
        self.unknown6 = 0
        self.levels = [None] * 7


    @classmethod
    def read(cls, file, decrypt=True, verify=True):
        """Read a T6RP file.

        Raise an exception if the file is invalid.
        Return a T6RP instance otherwise.

        Keyword arguments:
        decrypt -- whether or not to decrypt the file (default True)
        verify -- whether or not to verify the file's checksum (default True)
        """

        magic = file.read(4)
        assert magic == b'T6RP'

        replay = cls()

        replay.version, replay.character, replay.rank = unpack('<HBB', file.read(4))
        checksum, replay.unknown1, replay.unknown2, replay.key = unpack('<IBBB', file.read(7))

        # Decrypt data
        if decrypt:
            decrypted_file = BytesIO()
            file.seek(0)
            decrypted_file.write(file.read(15))
            decrypted_file.write(b''.join(chr((ord(c) - replay.key - 7*i) & 0xff) for i, c in enumerate(file.read())))
            file = decrypted_file
            file.seek(15)

        # Verify checksum
        if verify:
            data = file.read()
            file.seek(15)
            real_sum = (sum(ord(c) for c in data) + 0x3f000318 + replay.key) & 0xffffffff
            if checksum != real_sum:
                raise ChecksumError(checksum, real_sum)

        replay.unknown3, = unpack('<B', file.read(1))
        replay.date = file.read(9) #read_string(file, 9, 'ascii')
        replay.name = file.read(9) #read_string(file, 9, 'ascii').rstrip()
        replay.unknown4, replay.score, replay.unknown5, replay.slowdown, replay.unknown6 = unpack('<HIIfI', file.read(18))

        stages_offsets = unpack('<7I', file.read(28))

        for i, offset in enumerate(stages_offsets):
            if offset == 0:
                continue

            level = Level()
            replay.levels[i] = level

            file.seek(offset)
            (level.score, level.random_seed, level.point_items, level.power,
             level.lives, level.bombs, level.difficulty, level.unknown) = unpack('<IHHBbbBI', file.read(16))

            while True:
                time, keys, unknown = unpack('<IHH', file.read(8))

                if time == 9999999:
                    break

                level.keys.append((time, keys, unknown))

        return replay


    def write(self, file, encrypt=True):
        if encrypt:
            encrypted_file = file
            file = BytesIO()

        file.write(b'T6RP')
        file.write(pack('<HBB', self.version, self.character, self.rank))

        checksum_offset = file.tell()
        file.seek(4, 1) # For checksum
        file.write(pack('<BBB', self.unknown1, self.unknown2, self.key))

        file.write(pack('<B', self.unknown3))

        #TODO: find a more elegant method.
        n = 9 - len(self.date)
        file.write(self.date)
        file.write('\0' * n)
        n = 9 - len(self.name)
        file.write(self.name)
        file.write('\0' * n)

        file.write(pack('<HIIfI', self.unknown4, self.score, self.unknown5, self.slowdown, self.unknown6))

        stages_offsets_offset = file.tell()
        file.seek(7*4, 1) # Skip the stages offsets.

        stages_offsets = []
        for level in self.levels:
            if not level:
                stages_offsets.append(0)
                continue

            stages_offsets.append(file.tell())
            file.write(pack('<IHHBbbBI', level.score, level.random_seed,
                            level.point_items, level.power, level.lives,
                            level.bombs, level.difficulty, level.unknown))

            for time, keys, unknown in level.keys:
                file.write(pack('<IHH', time, keys, unknown))

            file.write(pack('<IHH', 9999999, 0, 0))

        file.seek(stages_offsets_offset)
        file.write(pack('<7I', *stages_offsets))

        # Write checksum
        file.seek(15)
        data = file.read()
        checksum = (sum(ord(c) for c in data) + 0x3f000318 + self.key) & 0xffffffff
        file.seek(checksum_offset)
        file.write(pack('<I', checksum))

        # Encrypt
        if encrypt:
            file.seek(0)
            encrypted_file.write(file.read(15))
            encrypted_file.write(b''.join(chr((ord(c) + self.key + 7*i) & 0xff) for i, c in enumerate(file.read())))

