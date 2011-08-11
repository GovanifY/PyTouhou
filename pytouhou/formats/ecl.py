from struct import pack, unpack
from pytouhou.utils.helpers import read_string

from collections import namedtuple


class ECL(object):
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
        for offset in sub_offsets:
            file.seek(offset)
            ecl.subs.append([])
            while True:
                time, opcode = unpack('<IH', file.read(6))
                if time == 0xffffffff or opcode == 0xffff:
                    break
                size, rank_mask, param_mask = unpack('<HHH', file.read(6))
                data = file.read(size - 12)
                #TODO: unpack data
                ecl.subs[-1].append((time, opcode, rank_mask, param_mask, data))

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

