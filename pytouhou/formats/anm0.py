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

"""ANM0 files handling.

This module provides classes for handling the ANM0 file format.
The ANM0 format is a format used in Touhou 6: EoSD to describe sprites
and animations.
Almost everything rendered in the game is described by an ANM0 file.
"""

from struct import pack, unpack
from pytouhou.utils.helpers import read_string, get_logger

from pytouhou.formats import WrongFormatError
from pytouhou.formats.animation import Animation
from pytouhou.formats.thtx import Texture


logger = get_logger(__name__)

#TODO: refactor/clean up


class Script(list):
    def __init__(self):
        list.__init__(self)
        self.interrupts = {}



class ANM0(Animation):
    _instructions = {0: {0: ('', 'delete'),
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
                         17: ('fff', 'set_3d_translation'),
                         18: ('fffi', 'move_to_linear'),
                         19: ('fffi', 'move_to_decel'),
                         20: ('fffi', 'move_to_accel'),
                         21: ('', 'wait'),
                         22: ('i', 'interrupt_label'),
                         23: ('', 'set_corner_relative_placement'),
                         24: ('', 'wait_ex'),
                         25: ('i', 'set_allow_offset'), #TODO: better name
                         26: ('i', 'set_automatic_orientation'),
                         27: ('f', 'shift_texture_x'),
                         28: ('f', 'shift_texture_y'),
                         29: ('i', 'set_visible'),
                         30: ('ffi', 'scale_in'),
                         31: ('i', None)},

                     2: {0: ('', 'noop'),
                         1: ('', 'delete'),
                         2: ('', 'keep_still'),
                         3: ('I', 'set_sprite'),
                         4: ('II', 'jump_bis'),
                         5: ('III', 'jump_ex'),
                         6: ('fff', 'set_3d_translation'),
                         7: ('ff', 'set_scale'),
                         8: ('I', 'set_alpha'),
                         9: ('BBBx', 'set_color'),
                         10: ('', 'toggle_mirrored'),
                         12: ('fff', 'set_3d_rotations'),
                         13: ('fff', 'set_3d_rotations_speed'),
                         14: ('ff', 'set_scale_speed'),
                         15: ('ii', 'fade'),
                         16: ('I', 'set_blendmode'),
                         17: ('fffi', 'move_to_linear'),
                         18: ('fffi', 'move_to_decel'),
                         19: ('fffi', 'move_to_accel'),
                         20: ('', 'wait'),
                         21: ('i', 'interrupt_label'),
                         22: ('', 'set_corner_relative_placement'),
                         23: ('', 'wait_ex'),
                         24: ('i', 'set_allow_offset'), #TODO: better name
                         25: ('i', 'set_automatic_orientation'),
                         26: ('f', 'shift_texture_x'),
                         27: ('f', 'shift_texture_y'),
                         28: ('i', 'set_visible'),
                         29: ('ffi', 'scale_in'),
                         30: ('i', None),
                         31: ('I', None),
                         32: ('IIfff', 'move_in_linear_bis'),
                         33: ('IIBBBx', 'change_color_in'),
                         34: ('III', 'fade_bis'),
                         35: ('IIfff', 'rotate_in_bis'),
                         36: ('IIff', 'scale_in_bis'),
                         37: ('II', 'set_int'),
                         38: ('ff', 'set_float'),
                         42: ('ff', 'decrement_float'),
                         50: ('fff', 'add_float'),
                         52: ('fff', 'substract_float'),
                         55: ('III', 'divide_int'),
                         59: ('II', 'set_random_int'),
                         60: ('ff', 'set_random_float'),
                         69: ('IIII', 'branch_if_not_equal'),
                         79: ('I', 'wait_duration'),
                         80: ('I', None)}}


    @classmethod
    def read(cls, file):
        anm_list = []
        start_offset = 0
        while True:
            file.seek(start_offset)
            nb_sprites, nb_scripts, zero1 = unpack('<III', file.read(12))
            width, height, fmt, unknown1 = unpack('<IIII', file.read(16))
            first_name_offset, unused, secondary_name_offset = unpack('<III', file.read(12))
            version, unknown2, texture_offset, has_data, next_offset, unknown3 = unpack('<IIIIII', file.read(24))

            if version == 0:
                assert zero1 == 0
                assert unknown3 == 0
                assert has_data == 0
            elif version == 2:
                assert zero1 == 0
                assert secondary_name_offset == 0
                assert has_data == 1 # Can be false but we don’t support that yet.
            else:
                raise WrongFormatError(version)

            instructions = cls._instructions[version]

            sprite_offsets = [unpack('<I', file.read(4))[0] for i in range(nb_sprites)]
            script_offsets = [unpack('<II', file.read(8)) for i in range(nb_scripts)]

            self = cls()

            self.size = (width, height)
            self.version = version

            # Names
            if first_name_offset:
                file.seek(start_offset + first_name_offset)
                self.first_name = read_string(file, 32, 'ascii') #TODO: 32, really?
            if secondary_name_offset:
                file.seek(start_offset + secondary_name_offset)
                self.secondary_name = read_string(file, 32, 'ascii') #TODO: 32, really?


            # Sprites
            for offset in sprite_offsets:
                file.seek(start_offset + offset)
                idx, x, y, width, height = unpack('<Iffff', file.read(20))
                self.sprites[idx] = x, y, width, height


            # Scripts
            for i, offset in script_offsets:
                self.scripts[i] = Script()
                instruction_offsets = []
                file.seek(start_offset + offset)
                while True:
                    instruction_offsets.append(file.tell() - (start_offset + offset))
                    if version == 0:
                        time, opcode, size = unpack('<HBB', file.read(4))
                    elif version == 2:
                        opcode, size, time, mask = unpack('<HHHH', file.read(8))
                        if opcode == 0xffff:
                            break
                        size -= 8
                    data = file.read(size)
                    if opcode in instructions:
                        args = unpack('<%s' % instructions[opcode][0], data)
                    else:
                        args = (data,)
                        logger.warn('unknown opcode %d', opcode)

                    self.scripts[i].append((time, opcode, args))
                    if version == 0 and opcode == 0:
                        break

                # Translate offsets to instruction pointers and register interrupts
                for instr_offset, (j, instr) in zip(instruction_offsets, enumerate(self.scripts[i])):
                    time, opcode, args = instr
                    if version == 0:
                        if opcode == 5:
                            args = (instruction_offsets.index(args[0]),)
                        elif opcode == 22:
                            interrupt = args[0]
                            self.scripts[i].interrupts[interrupt] = j + 1
                    elif version == 2:
                        if opcode == 4:
                            args = (instruction_offsets.index(args[0]), args[1])
                        elif opcode == 5:
                            args = (args[0], instruction_offsets.index(args[1]), args[2])
                        elif opcode == 21:
                            interrupt = args[0]
                            self.scripts[i].interrupts[interrupt] = j + 1
                        elif opcode == 69:
                            args = (args[0], args[1], instruction_offsets.index(args[2]), args[3])
                    self.scripts[i][j] = time, opcode, args

            # Texture
            if has_data:
                file.seek(start_offset + texture_offset)
                magic = file.read(4)
                assert magic == b'THTX'
                zero, fmt, width, height, size = unpack('<HHHHI', file.read(12))
                assert zero == 0
                data = file.read(size)
                self.texture = Texture(width, height, fmt, data)

            anm_list.append(self)

            if next_offset:
                start_offset += next_offset
            else:
                break

        return anm_list
