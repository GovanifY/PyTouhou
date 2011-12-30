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

from struct import Struct, unpack
from pytouhou.utils.pe import PEFile

from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)


SQ2 = 2. ** 0.5 / 2.


class Shot(object):
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


class SHT(object):
    def __init__(self):
        #self.unknown1 = None
        #self.bombs = 0.
        #self.unknown2 = None
        self.hitbox = 4.
        self.graze_hitbox = 42.
        self.autocollection_speed = 8.
        self.item_hitbox = 38.
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
                            if section.Name.startswith('.data')][0]
        text_section = [section for section in pe_file.sections
                            if section.Name.startswith('.text')][0]
        data_va = pe_file.image_base + data_section.VirtualAddress
        data_size = data_section.SizeOfRawData
        text_va = pe_file.image_base + text_section.VirtualAddress
        text_size = text_section.SizeOfRawData

        # Search the whole data segment for 4 successive character definitions
        for addr in xrange(data_va, data_va + data_size, 4):
            for character_id in xrange(4):
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
                pe_file.seek_to_va(ptr1 + 4)
                shtptr1, = unpack('<I', pe_file.file.read(4))
                pe_file.seek_to_va(ptr2 + 4)
                shtptr2, = unpack('<I', pe_file.file.read(4))
                if not (0 <= shtptr1 - data_va < data_size - 12
                        and 0 <= shtptr2 - data_va < data_size - 12):
                    break

                # It is unlikely this character record is *not* valid, but
                # just to be sure, let's check the first SHT definition.
                pe_file.seek_to_va(shtptr1)
                nb_shots, power, shotsptr = unpack('<III', pe_file.file.read(12))
                if not (0 < nb_shots <= 1000
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

        character_records_va = list(cls.find_character_defs(pe_file))[0]

        characters = []
        shots_offsets = []
        for character in xrange(4):
            sht = cls()

            pe_file.seek_to_va(character_records_va + 6*4*character)

            data = unpack('<4f2I', file.read(6*4))
            (speed, speed_focused, speed_unknown1, speed_unknown2,
             shots_func_offset, shots_func_offset_focused) = data

            sht.horizontal_vertical_speed = speed
            sht.horizontal_vertical_focused_speed = speed_focused
            sht.diagonal_speed = speed * SQ2
            sht.diagonal_focused_speed = speed_focused * SQ2

            # Read from “push” operand
            pe_file.seek_to_va(shots_func_offset + 4)
            offset = unpack('<I', file.read(4))[0]
            shots_offsets.append(offset)

            characters.append(sht)

        character = 0
        for shots_offset in shots_offsets:
            pe_file.seek_to_va(shots_offset)

            level_count = 9
            levels = []
            for i in xrange(level_count):
                shots_count, power, offset = unpack('<III', file.read(3*4))
                levels.append((shots_count, power, offset))

            sht = characters[character]
            sht.shots = {}

            for shots_count, power, offset in levels:
                sht.shots[power] = []
                pe_file.seek_to_va(offset)

                for i in xrange(shots_count):
                    shot = Shot()

                    data = unpack('<HH6fHBBhh', file.read(36))
                    (shot.interval, shot.delay, x, y, hitbox_x, hitbox_y,
                     shot.angle, shot.speed, shot.damage, shot.orb, shot.type,
                     shot.sprite, shot.unknown1) = data

                    shot.pos = (x, y)
                    shot.hitbox = (hitbox_x, hitbox_y)

                    sht.shots[power].append(shot)

            character += 1


        return characters

