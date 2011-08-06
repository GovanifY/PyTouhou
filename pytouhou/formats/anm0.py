from struct import pack, unpack
from pytouhou.utils.helpers import read_string

#TODO: refactor/clean up


class Animations(object):
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
        anm.scripts = {}#[None] * nb_scripts
        for i, offset in script_offsets:
            anm.scripts[i] = []
            file.seek(offset)
            while True:
                #TODO
                time, instr_type, length = unpack('<HBB', file.read(4))
                if instr_type == 0:
                    break
                data = file.read(length)
                anm.scripts[i].append((time, instr_type, data))
        #TODO

        return anm

