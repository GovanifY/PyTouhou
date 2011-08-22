from struct import pack, unpack
from pytouhou.utils.helpers import read_string

from collections import namedtuple


class ECL(object):
    _instructions = {0: ('', 'noop?'),
                     1: ('I', 'delete?'),
                     2: ('Ii', 'relative_jump'),
                     3: ('Iii', 'relative_jump_ex'),
                     4: ('ii', 'set_int'),
                     5: ('if', 'set_float'),
                     6: ('ii', 'set_random_int'),
                     8: ('if', 'set_random_float'),
                     9: ('iff', None),
                     10: ('i', None),
                     13: ('iii', None),
                     14: ('iii', None),
                     15: ('iii', None),
                     16: ('iii', None),
                     17: ('iii', None),
                     18: ('i', None),
                     20: ('iff', 'add'),
                     21: ('iff', 'sub'),
                     23: ('iff', None),
                     25: ('iffff', None),
                     26: ('i', None),
                     27: ('ii', 'compare_ints'),
                     28: ('ff', None),
                     29: ('ii', None),
                     30: ('ii', None),
                     31: ('ii', 'relative_jump_if_equal'),
                     32: ('ii', None),
                     33: ('ii', None),
                     34: ('ii', None),
                     35: ('iif', 'call'),
                     36: ('', 'return?'),
                     39: ('iifii', 'call_if_equal'),
                     43: ('fff', 'set_position'),
                     45: ('ff', 'set_angle_and_speed'),
                     46: ('f', 'set_rotation_speed'),
                     47: ('f', 'set_speed'),
                     48: ('f', 'set_acceleration'),
                     49: ('ff', None),
                     50: ('ff', None),
                     51: ('ff', 'set_speed_towards_player'),
                     52: ('iff', None),
                     56: ('iffi', None),
                     57: ('ifff', 'move_to'),
                     59: ('iffi', 'move_to2'),
                     61: ('i', 'stop_in'),
                     63: ('i', None),
                     65: ('ffff', None),
                     66: ('', None),
                     67: ('hhiiffffi', 'set_bullet_attributes'),
                     68: ('hhiiffffi', 'set_bullet_attributes2'),
                     69: ('hhiiffffi', 'set_bullet_attributes3'),
                     70: ('hhiiffffi', 'set_bullet_attributes4'),
                     71: ('hhiiffffi', 'set_bullet_attributes5'),
                     74: ('hhiiffffi', 'set_bullet_attributes6'),
                     75: ('hhiiffffi', 'set_bullet_attributes7'),
                     76: ('i', None),
                     77: ('i', 'set_bullet_interval'),
                     78: ('', 'delay_attack'),
                     79: ('', 'no_delay_attack'),
                     81: ('fff', 'set_bullet_launch_offset'),
                     82: ('iiiiffff', None),
                     83: ('', None),
                     84: ('i', None),
                     85: ('hhffffffiiiiii', 'laser'),
                     86: ('hhffffffiiiiii', 'laser2'),
                     87: ('i', 'set_upcoming_id'),
                     88: ('if','alter_laser_angle'),
                     90: ('iiii', None),
                     92: ('i', None),
                     #93: set_spellcard, a string is there
                     94: ('', None),
                     95: ('ifffhhi', None),
                     96: ('', None),
                     97: ('i', 'set_anim'),
                     98: ('hhhhhxx', 'set_multiple_anims'),
                     99: ('ii', None),
                     100: ('i', 'set_death_anim'),
                     101: ('i', 'set_boss_mode?'),
                     102: ('iffff', None),
                     103: ('fff', 'set_enemy_hitbox'),
                     104: ('i', None),
                     105: ('i', 'set_vulnerable'),
                     106: ('i', 'play_sound'),
                     107: ('i', None),
                     108: ('i', 'set_death_callback?'),
                     109: ('ii', 'memory_write_int'),
                     111: ('i', 'set_life'),
                     112: ('i', None),
                     113: ('i', 'set_low_life_trigger'),
                     114: ('i', 'set_low_life_callback'),
                     115: ('i', 'set_timeout'),
                     116: ('i', None),
                     117: ('i', None),
                     118: ('iihh', None),
                     119: ('i', 'drop_bonus'),
                     120: ('i', None),
                     121: ('ii', None),
                     122: ('i', None),
                     123: ('i', None),
                     124: ('i', None),
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

    def __init__(self):
        self.main = []
        self.subs = [[]]


    @classmethod
    def read(cls, file):
        sub_count, main_offset = unpack('<II', file.read(8))
        if file.read(8) != b'\x00\x00\x00\x00\x00\x00\x00\x00':
            raise Exception #TODO
        sub_offsets = unpack('<%s' % ('I' * sub_count), file.read(4 * sub_count))

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
                    args = unpack('<%s' % cls._instructions[opcode][0], data)
                else:
                    args = (data, )
                    print('Warning: unknown opcode %d' % opcode) #TODO

                ecl.subs[-1].append((time, opcode, rank_mask, param_mask, args))


            # Translate offsets to instruction pointers
            for instr_offset, (i, instr) in zip(instruction_offsets, enumerate(ecl.subs[-1])):
                time, opcode, rank_mask, param_mask, args = instr
                if opcode == 2: # relative_jump
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
            sub, instr_type, size = unpack('<HHH', file.read(6))
            data = file.read(size - 8)
            if instr_type in (0, 2, 4, 6): # Enemy spawn
                args = unpack('<ffIhHHH', data)
            else:
                print('ECL: Warning: unknown opcode %d (%r)' % (instr_type, data)) #TODO
                args = (data,)
            ecl.main.append((time, sub, instr_type, args))

        return ecl

