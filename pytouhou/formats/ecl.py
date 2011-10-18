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

import struct
from struct import pack, unpack, calcsize

from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)

class ECL(object):
    _instructions = {0: ('', 'noop?'),
                     1: ('I', 'delete?'),
                     2: ('Ii', 'relative_jump'),
                     3: ('Iii', 'relative_jump_ex'),
                     4: ('ii', 'set_int'),
                     5: ('if', 'set_float'),
                     6: ('ii', 'set_random_int'),
                     8: ('if', 'set_random_float'),
                     9: ('iff', 'set_random_float2'),
                     10: ('i', 'store_x'),
                     13: ('iii', 'add_int'),
                     14: ('iii', 'substract_int'),
                     15: ('iii', 'multiply_int'),
                     16: ('iii', 'divide_int'),
                     17: ('iii', 'modulo'),
                     18: ('i', 'increment'),
                     20: ('iff', 'add_float'),
                     21: ('iff', 'substract_float'),
                     23: ('iff', 'divide_float'),
                     25: ('iffff', 'get_direction'),
                     26: ('i', None),
                     27: ('ii', 'compare_ints'),
                     28: ('ff', 'compare_floats'),
                     29: ('ii', 'relative_jump_if_lower_than'),
                     30: ('ii', 'relative_jump_if_lower_or_equal'),
                     31: ('ii', 'relative_jump_if_equal'),
                     32: ('ii', 'relative_jump_if_greater_than'),
                     33: ('ii', 'relative_jump_if_greater_or_equal'),
                     34: ('ii', 'relative_jump_if_not_equal'),
                     35: ('iif', 'call'),
                     36: ('', 'return?'),
                     39: ('iifii', 'call_if_equal'),
                     43: ('fff', 'set_position'),
                     45: ('ff', 'set_angle_and_speed'),
                     46: ('f', 'set_rotation_speed'),
                     47: ('f', 'set_speed'),
                     48: ('f', 'set_acceleration'),
                     49: ('ff', 'set_random_angle'),
                     50: ('ff', 'set_random_angle_ex'),
                     51: ('ff', 'set_speed_towards_player'),
                     52: ('iff', 'move_in_decel'),
                     56: ('ifff', 'move_to_linear'),
                     57: ('ifff', 'move_to_decel'),
                     59: ('iffi', 'move_to_accel'),
                     61: ('i', 'stop_in'),
                     63: ('i', 'stop_in_accel'),
                     65: ('ffff', 'set_screen_box'),
                     66: ('', 'clear_screen_box'),
                     67: ('hhiiffffi', 'set_bullet_attributes'),
                     68: ('hhiiffffi', 'set_bullet_attributes2'),
                     69: ('hhiiffffi', 'set_bullet_attributes3'),
                     70: ('hhiiffffi', 'set_bullet_attributes4'),
                     71: ('hhiiffffi', 'set_bullet_attributes5'),
                     74: ('hhiiffffi', 'set_bullet_attributes6'),
                     75: ('hhiiffffi', 'set_bullet_attributes7'),
                     76: ('i', 'set_bullet_interval'),
                     77: ('i', 'set_bullet_interval_ex'),
                     78: ('', 'delay_attack'),
                     79: ('', 'no_delay_attack'),
                     81: ('fff', 'set_bullet_launch_offset'),
                     82: ('iiiiffff', 'set_extended_bullet_attributes'),
                     83: ('', None),
                     84: ('i', None),
                     85: ('hhffffffiiiiii', 'laser'),
                     86: ('hhffffffiiiiii', 'laser2'),
                     87: ('i', 'set_upcoming_id'),
                     88: ('if','alter_laser_angle'),
                     90: ('iiii', None),
                     92: ('i', None),
                     93: ('hhs', 'set_spellcard'),
                     94: ('', 'end_spellcard'),
                     95: ('ifffhhi', None),
                     96: ('', None),
                     97: ('i', 'set_anim'),
                     98: ('hhhhhxx', 'set_multiple_anims'),
                     99: ('ii', None),
                     100: ('i', 'set_death_anim'),
                     101: ('i', 'set_boss_mode?'),
                     102: ('iffff', 'create_squares'),
                     103: ('fff', 'set_enemy_hitbox'),
                     104: ('i', 'set_collidable'),
                     105: ('i', 'set_damageable'),
                     106: ('i', 'play_sound'),
                     107: ('i', 'set_death_flags'),
                     108: ('i', 'set_death_callback?'),
                     109: ('ii', 'memory_write_int'),
                     111: ('i', 'set_life'),
                     112: ('i', 'set_ellapsed_time'),
                     113: ('i', 'set_low_life_trigger'),
                     114: ('i', 'set_low_life_callback'),
                     115: ('i', 'set_timeout'),
                     116: ('i', 'set_timeout_callback'),
                     117: ('i', 'set_touchable'),
                     118: ('iihh', None),
                     119: ('i', 'drop_bonus'),
                     120: ('i', 'set_automatic_orientation'),
                     121: ('ii', 'call_special_function'),
                     122: ('i', None),
                     123: ('i', 'skip_frames'),
                     124: ('i', 'drop_specific_bonus'),
                     125: ('', None),
                     126: ('i', 'set_remaining_lives'),
                     127: ('i', None),
                     128: ('i', None),
                     129: ('ii', None),
                     130: ('i', None),
                     131: ('ffiiii', None),
                     132: ('i', None),
                     133: ('', None),
                     134: ('', None),
                     135: ('i', None)} #TODO

    _main_instructions = {0: ('fffhhHH', 'spawn_enemy'),
                          2: ('fffhhHH', 'spawn_enemy_mirrored'),
                          4: ('fffhhHH', 'spawn_enemy_random'),
                          6: ('fffhhHH', 'spawn_enemy_mirrored_random'),
                          8: ('', None),
                          9: ('', None),
                          10: ('II', None),
                          12: ('', None)}


    def __init__(self):
        self.main = []
        self.subs = [[]]


    @classmethod
    def read(cls, file):
        sub_count, main_offset = unpack('<II', file.read(8))
        if file.read(8) != b'\x00\x00\x00\x00\x00\x00\x00\x00':
            raise Exception #TODO
        sub_offsets = unpack('<%dI' % sub_count, file.read(4 * sub_count))

        ecl = cls()
        ecl.subs = []
        ecl.main = []

        # Read subs
        for sub_offset in sub_offsets:
            file.seek(sub_offset)
            ecl.subs.append([])

            instruction_offsets = []

            while True:
                instruction_offsets.append(file.tell() - sub_offset)

                time, opcode = unpack('<IH', file.read(6))
                if time == 0xffffffff or opcode == 0xffff:
                    break
                size, rank_mask, param_mask = unpack('<HHH', file.read(6))
                data = file.read(size - 12)
                if opcode in cls._instructions:
                    fmt = '<%s' % cls._instructions[opcode][0]
                    if fmt.endswith('s'):
                        fmt = fmt[:-1]
                        fmt = '%s%ds' % (fmt, size - 12 - calcsize(fmt))
                    args = unpack(fmt, data)
                    if fmt.endswith('s'):
                        args = args[:-1] + (args[-1].decode('shift_jis'),)
                else:
                    args = (data, )
                    logger.warn('unknown opcode %d', opcode)

                ecl.subs[-1].append((time, opcode, rank_mask, param_mask, args))


            # Translate offsets to instruction pointers
            for instr_offset, (i, instr) in zip(instruction_offsets, enumerate(ecl.subs[-1])):
                time, opcode, rank_mask, param_mask, args = instr
                if opcode in (2, 29, 30, 31, 32, 33, 34): # relative_jump
                    frame, relative_offset = args
                    args = frame, instruction_offsets.index(instr_offset + relative_offset)
                elif opcode == 3: # relative_jump_ex
                    frame, relative_offset, counter_id = args
                    args = frame, instruction_offsets.index(instr_offset + relative_offset), counter_id
                ecl.subs[-1][i] = time, opcode, rank_mask, param_mask, args


        # Read main
        file.seek(main_offset)
        while True:
            time, = unpack('<H', file.read(2))
            if time == 0xffff:
                break

            sub, opcode, size = unpack('<HHH', file.read(6))
            data = file.read(size - 8)

            if opcode in cls._main_instructions:
                args = unpack('<%s' % cls._main_instructions[opcode][0], data)
            else:
                args = (data,)
                logger.warn('unknown main opcode %d', opcode)

            ecl.main.append((time, sub, opcode, args))

        return ecl


    def write(self, file):
        sub_count = len(self.subs)
        sub_offsets = []
        main_offset = 0

        # Skip header, it will be written later
        file.seek(8+8+4*sub_count)

        # Write subs
        for sub in self.subs:
            sub_offsets.append(file.tell())

            instruction_offsets = []
            instruction_datas = []
            for time, opcode, rank_mask, param_mask, args in sub:
                format = self._instructions[opcode][0]
                if format.endswith('s'):
                    args = list(args)
                    args[-1] = args[-1].encode('shift_jis')
                    format = '%s%ds' % (format[:-1], len(args[-1]))
                format = '<IHHHH%s' % format
                size = calcsize(format)
                instruction_offsets.append((instruction_offsets[-1] + len(instruction_datas[-1])) if instruction_offsets else 0)
                try:
                    instruction_datas.append(pack(format, time, opcode, size, rank_mask, param_mask, *args))
                except struct.error:
                    logger.error('Failed to assemble opcode %d' % opcode)
                    raise

            #TODO: clean up this mess
            for instruction, data, offset in zip(sub, instruction_datas, instruction_offsets):
                time, opcode, rank_mask, param_mask, args = instruction
                if opcode in (2, 29, 30, 31, 32, 33, 34): # relative_jump
                    frame, index = args
                    args = frame, instruction_offsets[index] - offset
                    format = '<IHHHH%s' % self._instructions[opcode][0]
                    size = calcsize(format)
                    data = pack(format, time, opcode, size, rank_mask, param_mask, *args)
                elif opcode == 3: # relative_jump_ex
                    frame, index, counter_id = args
                    args = frame, instruction_offsets[index] - offset, counter_id
                    format = '<IHHHH%s' % self._instructions[opcode][0]
                    size = calcsize(format)
                    data = pack(format, time, opcode, size, rank_mask, param_mask, *args)
                file.write(data)
            file.write(b'\xff' * 6 + b'\x0c\x00\x00\xff\xff\x00')

        # Write main
        main_offset = file.tell()
        for time, sub, opcode, args in self.main:
            format = '<HHHH%s' % self._main_instructions[opcode][0]
            size = calcsize(format)

            file.write(pack(format, time, sub, opcode, size, *args))
        file.write(b'\xff\xff\x04\x00')

        # Patch header
        file.seek(0)
        file.write(pack('<IIII%dI' % sub_count, sub_count, main_offset, 0, 0, *sub_offsets))

