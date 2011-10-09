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


from math import cos, sin, atan2, pi


class Item(object):
    def __init__(self, pos, item_type, angle, speed, player, game):
        self._game = game
        self._sprite = item_type.sprite
        self._removed = False
        self._item_type = item_type

        self.hitbox_half_size = item_type.hitbox_size / 2.

        self.frame = 0

        self.player = player

        self.x, self.y = pos
        self.angle = angle
        self.speed = speed
        dx, dy = cos(angle) * speed, sin(angle) * speed
        self.delta = dx, dy

        self._sprite.angle = angle


    def collect(self, player):
        player.state.score += self._item_type.score
        self._removed = True


    def update(self):
        dx, dy = self.delta

        if self.player is not None:
            self.angle = atan2(self.player.y - self.y, self.player.x - self.x)
            dx, dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed
        else:
            pass #TODO: item falls!

        self.x += dx
        self.y += dy

