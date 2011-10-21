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



class Effect(object):
    def __init__(self, pos, index, anm_wrapper):
        self._sprite = Sprite()
        self._anmrunner = ANMRunner(anm_wrapper, index, self._sprite)
        self._anmrunner.run_frame()
        self._removed = False

        self.x, self.y = pos

    def update(self):
        if self._anmrunner and not self._anmrunner.run_frame():
            self._anmrunner = None

        if self._sprite:
            if self._sprite._removed:
                self._sprite = None
