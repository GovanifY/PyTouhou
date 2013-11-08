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

from pytouhou.vm import ANMRunner


class Orb(Element):
    def __init__(self, anm, index, player):
        Element.__init__(self)

        self.sprite = Sprite()
        self.anmrunner = ANMRunner(anm, index, self.sprite)

        self.offset_x = 0
        self.offset_y = 0

        self.player = player


    def update(self):
        self.anmrunner.run_frame()
        self.x = self.player.x + self.offset_x
        self.y = self.player.y + self.offset_y
