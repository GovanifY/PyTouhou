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


class Player(object):
    def __init__(self):
        self.x = 192.0
        self.y = 384.0
        self.score = 0
        self.graze = 0
        self.power = 0
        self.lives = 0
        self.bombs = 0
        self.character = 0 # ReimuA/ReimuB/MarisaA/MarisaB/...
