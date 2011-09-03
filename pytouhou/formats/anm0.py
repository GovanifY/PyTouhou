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

from struct import pack, unpack
from pytouhou.utils.helpers import read_string, get_logger


logger = get_logger(__name__)

#TODO: refactor/clean up


class Animations(object):
    _instructions = {0: ('', 'delete'),
                     1: ('I', 'set_sprite'),
                     2: ('ff', 'set_scale'),
                     3: ('I', 'set_alpha'),
                     4: ('BBBx', 'set_color'),
                     5: ('I', 'jump'),
                     7: ('', 'toggle_mirrored'),
                     9: ('fff', 'set_3d_rotations'),
                     10: ('fff', 'set_3d_rotations_speed'),
                     11: ('ff', 'set_scale_speed'),
                     12: ('ii', 'fade'),
                     13: ('', 'set_blendmode_add'),
                     14: ('', 'set_blendmode_alphablend'),
                     15: ('', 'keep_still'),
                     16: ('ii', 'set_random_sprite'),
                     17: ('fff', None),
                     18: ('ffii', None),
                     19: ('ffii', None),
                     20: ('fffi', None),
                     21: ('', None),
                     22: ('i', None),
                     23: ('', 'set_corner_relative_placement'),
                     24: ('', None),
                     25: ('i', 'set_allow_offset'), #TODO: better name
                     26: ('i', None),
                     27: ('f', 'shift_texture_x'),
                     28: ('f', 'shift_texture_y'),
                     30: ('ffi', 'scale_in'),
                     31: ('i', None)}


    def __init__(self):
        self.size = (0, 0)
        self.first_name = None
        self.secondary_name = None
        self.sprites = {}
        self.scripts = {}


    @classmethod
    def read(cls, file):
        nb_sprites, nb_scripts, zero1 = unpack('<III', file.read(12))
        width, height, format, zero2 = unpack('<IIII', file.read(16))
        first_name_offset, unused, secondary_name_offset = unpack('<III', file.read(12))
        version, unknown1, thtxoffset, hasdata, nextoffset = unpack('<IIIII', file.read(20))
        if version != 0:
            raise Exception #TODO
        file.read(4) #TODO

        sprite_offsets = [unpack('<I', file.read(4))[0] for i in range(nb_sprites)]
        script_offsets = [unpack('<II', file.read(8)) for i in range(nb_scripts)]

        anm = Animations()

        anm.size = (width, height)

        # Names
        if first_name_offset:
            file.seek(first_name_offset)
            anm.first_name = read_string(file, 32, 'ascii') #TODO: 32, really?
        if secondary_name_offset:
            file.seek(secondary_name_offset)
            anm.secondary_name = read_string(file, 32, 'ascii') #TODO: 32, really?


        # Sprites
        file.seek(64)
        anm.sprites = {}
        for offset in sprite_offsets:
            file.seek(offset)
            idx, x, y, width, height = unpack('<Iffff', file.read(20))
            anm.sprites[idx] = x, y, width, height


        # Scripts
        anm.scripts = {}
        for i, offset in script_offsets:
            anm.scripts[i] = []
            instruction_offsets = []
            file.seek(offset)
            while True:
                #TODO
                instruction_offsets.append(file.tell() - offset)
                time, opcode, length = unpack('<HBB', file.read(4))
                data = file.read(length)
                if opcode in cls._instructions:
                    args = unpack('<%s' % cls._instructions[opcode][0], data)
                else:
                    args = (data,)
                    logger.warn('unknown opcode %d', opcode)

                anm.scripts[i].append((time, opcode, args))
                if opcode == 0:
                    break

            # Translate offsets to instruction pointers
            for instr_offset, (j, instr) in zip(instruction_offsets, enumerate(anm.scripts[i])):
                time, opcode, args = instr
                if opcode == 5:
                    args = (instruction_offsets.index(args[0]),)
                anm.scripts[i][j] = time, opcode, args
        #TODO

        return anm

