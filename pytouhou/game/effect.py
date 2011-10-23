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
from pytouhou.utils.interpolator import Interpolator
from math import pi



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


class Particle(object):
    def __init__(self, start_pos, index, anm_wrapper, size, end_pos):
        self._sprite = Sprite()
        self._sprite.anm, self._sprite.texcoords = anm_wrapper.get_sprite(index)
        self._removed = False

        self.x, self.y = start_pos
        self.frame = 0
        self._sprite.alpha = 128
        self._sprite.blendfunc = 1

        self.pos_interpolator = Interpolator(start_pos, 0,
                                             end_pos, 24, formula=(lambda x: 2. * x - x ** 2))
        self.scale_interpolator = Interpolator((size, size), 0,
                                               (0., 0.), 24)
        self.rotations_interpolator = Interpolator((0., 0., 0.), 0,
                                                   (0., 0., 2*pi), 24)
        self._sprite._changed = True


    def update(self):
        self.pos_interpolator.update(self.frame)
        self.x, self.y = self.pos_interpolator.values

        self.scale_interpolator.update(self.frame)
        self._sprite.rescale = self.scale_interpolator.values

        self.rotations_interpolator.update(self.frame)
        self._sprite.rotations_3d = self.rotations_interpolator.values

        self._sprite._changed = True

        if self.frame == 24:
            self._removed = True

        self.frame += 1
