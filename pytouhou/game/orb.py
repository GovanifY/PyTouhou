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


from pytouhou.game.sprite import Sprite
from pytouhou.vm.anmrunner import ANMRunner


class Orb(object):
    __slots__ = ('_sprite', '_anmrunner', 'offset_x', 'offset_y', 'player_state',
                 'fire')

    def __init__(self, anm_wrapper, index, player_state, fire_func):
        self._sprite = Sprite()
        self._anmrunner = ANMRunner(anm_wrapper, index, self._sprite)
        self._anmrunner.run_frame()

        self.offset_x = 0
        self.offset_y = 0

        self.player_state = player_state
        self.fire = fire_func


    @property
    def x(self):
        return self.player_state.x + self.offset_x


    @property
    def y(self):
        return self.player_state.y + self.offset_y


    def update(self):
        self._anmrunner.run_frame()
