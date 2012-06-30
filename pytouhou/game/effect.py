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
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(anm_wrapper, index, self.sprite)
        self.anmrunner.run_frame()
        self.removed = False

        self.x, self.y = pos


    def update(self):
        if self.anmrunner and not self.anmrunner.run_frame():
            self.anmrunner = None

        if self.sprite:
            if self.sprite.removed:
                self.sprite = None
                self.removed = True



class Particle(object):
    def __init__(self, start_pos, index, anm_wrapper, size, amp, game):
        self._game = game

        self.sprite = Sprite()
        self.sprite.anm, self.sprite.texcoords = anm_wrapper.get_sprite(index)
        self.removed = False

        self.x, self.y = start_pos
        self.frame = 0
        self.sprite.alpha = 128
        self.sprite.blendfunc = 1
        self.sprite.rescale = (size, size)

        self.pos_interpolator = None
        self.scale_interpolator = None
        self.rotations_interpolator = None
        self.alpha_interpolator = None

        self.amp = amp


    def set_end_pos(self, amp):
        end_pos = (self.x + amp * self._game.prng.rand_double() - amp/2,
                   self.y + amp * self._game.prng.rand_double() - amp/2)

        self.pos_interpolator = Interpolator((self.x, self.y), 0,
                                             end_pos, 24, formula=(lambda x: 2. * x - x ** 2))
        self.scale_interpolator = Interpolator(self.sprite.rescale, 0,
                                               (0., 0.), 24)
        self.rotations_interpolator = Interpolator(self.sprite.rotations_3d, 0,
                                                   (0., 0., 2*pi), 24)
        self.alpha_interpolator = Interpolator((self.sprite.alpha,), 0,
                                               (0.,), 24)


    def update(self):
        if self.frame == 0:
            self.set_end_pos(self.amp)

        if self.pos_interpolator:
            self.pos_interpolator.update(self.frame)
            self.x, self.y = self.pos_interpolator.values

            self.scale_interpolator.update(self.frame)
            self.sprite.rescale = self.scale_interpolator.values

            self.rotations_interpolator.update(self.frame)
            self.sprite.rotations_3d = self.rotations_interpolator.values

            self.alpha_interpolator.update(self.frame)
            self.sprite.alpha, = self.alpha_interpolator.values

            self.sprite.changed = True

        if self.frame == 24:
            self.removed = True

        self.frame += 1

