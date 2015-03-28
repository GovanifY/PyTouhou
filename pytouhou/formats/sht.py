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

from struct import unpack

from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)


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
        self.unknown2 = None
        self.unknown3 = None
        self.unknown4 = None
        self.unknown5 = None


class SHT:
    def __init__(self):
        self.unknown1 = None
        self.bombs = 0.
        self.unknown2 = None
        self.hitbox = 0.
        self.graze_hitbox = 0.
        self.autocollection_speed = 0.
        self.item_hitbox = 0.
        self.percentage_of_cherry_loss_on_die = 0.
        self.point_of_collection = 0
        self.horizontal_vertical_speed = 0.
        self.horizontal_vertical_focused_speed = 0.
        self.diagonal_speed = 0.
        self.diagonal_focused_speed = 0.
        self.shots = {}


    @classmethod
    def read(cls, file):
        sht = cls()

        data = unpack('<hhfI10f', file.read(52))
        (sht.unknown1, level_count, sht.bombs, sht.unknown2, sht.hitbox,
         sht.graze_hitbox, sht.autocollection_speed, sht.item_hitbox,
         sht.percentage_of_cherry_loss_on_die, sht.point_of_collection,
         sht.horizontal_vertical_speed, sht.horizontal_vertical_focused_speed,
         sht.diagonal_speed, sht.diagonal_focused_speed) = data

        levels = []
        for i in range(level_count):
            offset, power = unpack('<II', file.read(8))
            levels.append((power, offset))

        sht.shots = {}

        for power, offset in levels:
            sht.shots[power] = []
            file.seek(offset)

            while True:
                interval, delay = unpack('<HH', file.read(4))
                if interval == 0xffff and delay == 0xffff:
                    break

                shot = Shot()

                shot.interval = interval
                shot.delay = delay

                data = unpack('<6fHBBhh4I', file.read(48))
                (x, y, hitbox_x, hitbox_y, shot.angle, shot.speed,
                 shot.damage, shot.orb, shot.shot_type, shot.sprite,
                 shot.unknown1, shot.unknown2, shot.unknown3, shot.unknown4,
                 shot.unknown5) = data

                shot.pos = (x, y)
                shot.hitbox = (hitbox_x, hitbox_y)

                sht.shots[power].append(shot)


        return sht

