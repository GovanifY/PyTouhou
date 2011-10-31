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

from struct import pack, unpack, calcsize
from pytouhou.utils.helpers import read_string

from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)

class MSG(object):
    _instructions = {0: ('', None),
                     1: ('hh', None),
                     2: ('hh', 'change_face'),
                     3: ('hhs', 'display_dialog_line'),
                     4: ('I', 'pause'),
                     5: ('hh', 'switch'),
                     6: ('', 'add_enemy_sprite'),
                     7: ('I', 'change_music'),
                     8: ('hhs', 'display_character_line'),
                     9: ('I', None),
                     10: ('', None),
                     11: ('', 'next_level'),
                     12: ('', None),
                     13: ('I', None),
                     14: ('', None)} #TODO


    def __init__(self):
        self.msgs = [[]]


    @classmethod
    def read(cls, file):
        entry_count, = unpack('<I', file.read(4))
        entry_offsets = unpack('<%dI' % entry_count, file.read(4 * entry_count))

        msg = cls()
        msg.msgs = []

        for offset in entry_offsets:
            if msg.msgs and offset == entry_offsets[0]: # In EoSD, Reimu’s scripts start at 0, and Marisa’s ones at 10.
                continue                                # If Reimu has less than 10 scripts, the remaining offsets are equal to her first.

            msg.msgs.append([])
            file.seek(offset)

            while True:
                time, opcode, size = unpack('<HBB', file.read(4))
                if time == 0 and opcode == 0:
                    break
                data = file.read(size)
                if opcode in cls._instructions:
                    fmt = '<%s' % cls._instructions[opcode][0]
                    if fmt.endswith('s'):
                        fmt = fmt[:-1]
                        fmt = '%s%ds' % (fmt, size - calcsize(fmt))
                    args = unpack(fmt, data)
                    if fmt.endswith('s'):
                        args = args[:-1] + (args[-1].decode('shift_jis'),)
                else:
                    args = (data, )
                    logger.warn('unknown msg opcode %d', opcode)

                msg.msgs[-1].append((time, opcode, args))


        return msg

