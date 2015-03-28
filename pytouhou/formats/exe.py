# -*- encoding: utf-8 -*-
##
## Copyright (C) 2011 Thibaut Girka <thib@sitedethib.com>
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

from copy import copy
from struct import Struct, unpack

from pytouhou.utils.pe import PEFile

from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)


SQ2 = 2. ** 0.5 / 2.


class InvalidExeException(Exception):
    pass


class Shot:
    def __init__(self):
        self.interval = 0
        self.delay = 0
        self.pos = (0., 0.)
        self.hitbox = (0., 0.)
        self.angle = 0.
        self.speed = 0.
        self.damage = 0
        self.orb = 0
        self.type = 0
        self.sprite = 0
        self.unknown1 = None


class SHT:
    def __init__(self):
        #self.unknown1 = None
        #self.bombs = 0.
        #self.unknown2 = None
        self.hitbox = 2.
        self.graze_hitbox = 21.
        self.autocollection_speed = 8.
        self.item_hitbox = 19.
        # No percentage_of_cherry_loss_on_die
        self.point_of_collection = 128 #TODO: find the real default.
        self.horizontal_vertical_speed = 0.
        self.horizontal_vertical_focused_speed = 0.
        self.diagonal_speed = 0.
        self.diagonal_focused_speed = 0.
        self.shots = {}


    @classmethod
    def find_character_defs(cls, pe_file):
        """Generator returning the possible VA of character definition blocks.

        Based on knowledge of the structure, it tries to find valid definition blocks
        without embedding any copyrighted material or hard-coded offsets that would
        only be useful for a specific build of the game.
        """

        format = Struct('<4f2I')
        data_section = [section for section in pe_file.sections
                            if section.Name.startswith(b'.data')][0]
        text_section = [section for section in pe_file.sections
                            if section.Name.startswith(b'.text')][0]
        data_va = pe_file.image_base + data_section.VirtualAddress
        data_size = data_section.SizeOfRawData
        text_va = pe_file.image_base + text_section.VirtualAddress
        text_size = text_section.SizeOfRawData

        # Search the whole data segment for 4 successive character definitions
        for addr in range(data_va, data_va + data_size, 4):
            for character_id in range(4):
                pe_file.seek_to_va(addr + character_id * 24)
                (speed1, speed2, speed3, speed4,
                 ptr1, ptr2) = format.unpack(pe_file.file.read(format.size))

                # Check whether the character's speed make sense,
                # and whether the function pointers point to valid addresses
                if not (all(0. < x < 10. for x in (speed1, speed2, speed3, speed4))
                        and speed2 <= speed1
                        and 0 <= ptr1 - text_va < text_size - 8
                        and 0 <= ptr2 - text_va < text_size - 8):
                    break

                # So far, this character definition seems to be valid.
                # Now, make sure the shoot function wrappers pass valid addresses

                # Search for the “push” instruction
                for i in range(20):
                    # Find the “push” instruction
                    pe_file.seek_to_va(ptr1 + i)
                    instr1, shtptr1 = unpack('<BI', pe_file.file.read(5))
                    pe_file.seek_to_va(ptr2 + i)
                    instr2, shtptr2 = unpack('<BI', pe_file.file.read(5))
                    if instr1 == 0x68 and instr2 == 0x68 and (0 <= shtptr1 - data_va < data_size - 12
                                                              and 0 <= shtptr2 - data_va < data_size - 12):
                        # It is unlikely this character record is *not* valid, but
                        # just to be sure, let's check the first SHT definition.
                        pe_file.seek_to_va(shtptr1)
                        nb_shots, power, shotsptr = unpack('<III', pe_file.file.read(12))
                        if (0 < nb_shots <= 1000
                            and 0 <= power < 1000
                            and 0 <= shotsptr - data_va < data_size - 36*nb_shots):
                            break
                # Check if everything is fine...
                if not (0 <= shtptr1 - data_va < data_size - 12
                        and 0 <= shtptr2 - data_va < data_size - 12
                        and 0 < nb_shots <= 1000
                        and 0 <= power < 1000
                        and 0 <= shotsptr - data_va < data_size - 36*nb_shots):
                    break

            else:
                # XXX: Obscure python feature! This only gets executed if the
                # XXX: loop ended without a break statement.
                # In our case, it's only executed if all the 4 character
                # definitions are considered valid.
                yield addr


    @classmethod
    def read(cls, file):
        pe_file = PEFile(file)
        data_section = [section for section in pe_file.sections
                            if section.Name.startswith(b'.data')][0]
        data_va = pe_file.image_base + data_section.VirtualAddress
        data_size = data_section.SizeOfRawData

        try:
            character_records_va = next(cls.find_character_defs(pe_file))
        except StopIteration:
            raise InvalidExeException

        characters = []
        shots_offsets = {}
        for character in range(4):
            sht = cls()

            pe_file.seek_to_va(character_records_va + 6*4*character)

            data = unpack('<4f2I', file.read(6*4))
            (speed, speed_focused, speed_unknown1, speed_unknown2,
             shots_func_offset, shots_func_offset_focused) = data

            sht.horizontal_vertical_speed = speed
            sht.horizontal_vertical_focused_speed = speed_focused
            sht.diagonal_speed = speed * SQ2
            sht.diagonal_focused_speed = speed_focused * SQ2

            # Characters might have different shot types whether they are
            # focused or not, but properties read earlier apply to both modes.
            focused_sht = copy(sht)
            characters.append((sht, focused_sht))

            for sht, func_offset in ((sht, shots_func_offset), (focused_sht, shots_func_offset_focused)):
                # Search for the “push” instruction
                for i in range(20):
                    # Find the “push” instruction
                    pe_file.seek_to_va(func_offset + i)
                    instr, offset = unpack('<BI', file.read(5))
                    if instr == 0x68 and 0 <= offset - data_va < data_size - 12:
                        pe_file.seek_to_va(offset)
                        nb_shots, power, shotsptr = unpack('<III', pe_file.file.read(12))
                        if (0 < nb_shots <= 1000
                            and 0 <= power < 1000
                            and 0 <= shotsptr - data_va < data_size - 36*nb_shots):
                            break
                if offset not in shots_offsets:
                    shots_offsets[offset] = []
                shots_offsets[offset].append(sht)

        for shots_offset, shts in shots_offsets.items():
            pe_file.seek_to_va(shots_offset)

            level_count = 9
            levels = []
            for i in range(level_count):
                shots_count, power, offset = unpack('<III', file.read(3*4))
                levels.append((shots_count, power, offset))

            shots = {}

            for shots_count, power, offset in levels:
                shots[power] = []
                pe_file.seek_to_va(offset)

                for i in range(shots_count):
                    shot = Shot()

                    data = unpack('<HH6fHBBhh', file.read(36))
                    (shot.interval, shot.delay, x, y, hitbox_x, hitbox_y,
                     shot.angle, shot.speed, shot.damage, shot.orb, shot.type,
                     shot.sprite, shot.unknown1) = data

                    shot.pos = (x, y)
                    shot.hitbox = (hitbox_x, hitbox_y)

                    shots[power].append(shot)

            for sht in shts:
                sht.shots = shots


        return characters

