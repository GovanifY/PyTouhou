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

from struct import unpack
from pytouhou.utils.helpers import read_string

from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)


class Level(object):
    def __init__(self):
        self.keys = []


class T6RP(object):
    def __init__(self):
        self.levels = []


    @classmethod
    def read(cls, file):
        if file.read(4) != b'T6RP':
            raise Exception
        if file.read(2) != b'\x02\x01':
            raise Exception

        replay = cls()

        replay.character, replay.rank, checksum, unknown, key, unknown = unpack('<BBHIBB', file.read(10))
        replay.date = read_string(file, 9, 'ascii')
        replay.name = read_string(file, 9, 'ascii').rstrip()
        unknown, replay.score, unknown, replay.slowdown, unknown = unpack('<HIIfI', file.read(18))

        stages_offsets = unpack('<7I', file.read(28))

        replay.levels = []

        for offset in stages_offsets:
            replay.levels.append(None)

            if offset == 0:
                continue

            level = Level()
            replay.levels[-1] = level

            file.seek(offset)
            level.score, level.random_seed, unknown, level.power, level.lives, level.bombs, level.difficulty, unknown = unpack('<IHHBbbBI', file.read(16))

            while True:
                time, keys, unknown = unpack('<IHH', file.read(8))

                if time == 9999999:
                    break

                level.keys.append((time, keys))

