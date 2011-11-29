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


class Shot(object):
    def __init__(self):
        self.interval = 0.
        self.unknown1 = None
        self.pos = (0., 0.)
        self.hitbox = (0., 0.)
        self.angle = 0.
        self.speed = 0.
        self.damage = 0
        self.orb = 0
        self.unknown2 = None
        self.sprite = 0
        self.unknown3 = None
        self.unknown4 = None
        self.homing = False
        self.unknown5 = None
        self.unknown6 = None


class SHT(object):
    def __init__(self):
        self.unknown1 = None
        self.level_count = 9
        self.bombs = 0.
        self.unknown2 = None
        self.hitbox = 0.
        self.graze_hitbox = 0.
        self.autocollected_item_speed = 0.
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
        (_, level_count, bombs, _, hitbox, graze_hitbox,
         autocollected_item_speed, item_hitbox, percentage_of_cherry_loss_on_die,
         point_of_collection, horizontal_vertical_speed,
         horizontal_vertical_focused_speed, diagonal_speed,
         diagonal_focused_speed) = unpack('<hhfI10f', file.read(52))

        levels = []
        for i in xrange(level_count):
            offset, power = unpack('<II', file.read(8))
            levels.append((power, offset))

        sht = cls()
        sht.shots = {}

        for power, offset in levels:
            sht.shots[power] = []
            file.seek(offset)

            while True:
                interval, unknown1 = unpack('<HH', file.read(4))
                if interval == 0xffff and unknown1 == 0xffff:
                    break

                shot = Shot()

                data = file.read(48)
                (x, y, hitbox_x, hitbox_y, shot.angle, shot.speed,
                 shot.damage, shot.orb, shot.unknown2, shot.sprite,
                 shot.unknown3, unknown4, homing, unknown5,
                 unknown6) = unpack('<6fHBBhh4I', data)

                shot.pos = (x, y)
                shot.hitbox = (hitbox_x, hitbox_y)
                shot.unknown4 = bool(unknown4)
                shot.homing = bool(homing)
                shot.unknown5 = bool(unknown5)
                shot.unknown6 = bool(unknown6)

                sht.shts[power].append(shot)


        return sht

