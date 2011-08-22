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
        anm.scripts = {}
        for i, offset in script_offsets:
            anm.scripts[i] = []
            instruction_offsets = []
            file.seek(offset)
            while True:
                #TODO
                instruction_offsets.append(file.tell() - offset)
                time, instr_type, length = unpack('<HBB', file.read(4))
                data = file.read(length)
                if instr_type == 1: # set_sprite
                    args = unpack('<I', data)
                elif instr_type == 2: # set_scale
                    args = unpack('<ff', data)
                elif instr_type == 3: # set_alpha
                    args = unpack('<I', data)
                elif instr_type == 5: # jump
                    # Translate offset to instruction index
                    args = (instruction_offsets.index(unpack('<I', data)[0]),)
                elif instr_type == 9: # set_3d_rotation
                    args = unpack('<fff', data)
                elif instr_type == 10: # set_3d_rotation_speed
                    args = unpack('<fff', data)
                elif instr_type == 27: # shift_texture_x
                    args = unpack('<f', data)
                elif instr_type == 28: # shift_texture_y
                    args = unpack('<f', data)
                else:
                    args = (data,)
                anm.scripts[i].append((time, instr_type, args))
                if instr_type == 0:
                    break
        #TODO

        return anm

