# -*- encoding: utf-8 -*-
##
## Copyright (C) 2014 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from math import radians
from pytouhou.formats.exe import SHT, Shot


player = SHT()
player.horizontal_vertical_speed = 2.
player.horizontal_vertical_focused_speed = 1.5
player.diagonal_speed = 1.5
player.diagonal_focused_speed = 1.

shot = Shot()
shot.interval = 10
shot.delay = 5
shot.pos = (0, -32)
shot.hitbox = (5, 5)
shot.angle = radians(-90)
shot.speed = 5.
shot.damage = 16
shot.orb = 0
shot.type = 2
shot.sprite = 64
shot.unknown1 = 0

# Dict of list of shots, each for one power level.
# Always define at least the shot for max power, usually 999.
player.shots[999] = [shot]

# List of (unfocused, focused) shot types.
characters = [(player, player)]
