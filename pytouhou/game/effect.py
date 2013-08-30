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


from pytouhou.game.element import Element
from pytouhou.game.sprite import Sprite
from pytouhou.vm.anmrunner import ANMRunner
from pytouhou.utils.interpolator import Interpolator



class Effect(Element):
    def __init__(self, pos, index, anm):
        Element.__init__(self, pos)
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(anm, index, self.sprite)


    def update(self):
        if self.anmrunner and not self.anmrunner.run_frame():
            self.anmrunner = None

        if self.sprite:
            if self.sprite.removed:
                self.sprite = None
                self.removed = True



class Particle(Effect):
    def __init__(self, pos, index, anm, amp, game, reverse=False, duration=24):
        Effect.__init__(self, pos, index, anm)

        self.frame = 0
        self.duration = duration

        random_pos = (self.x + amp * game.prng.rand_double() - amp / 2,
                      self.y + amp * game.prng.rand_double() - amp / 2)

        if not reverse:
            self.pos_interpolator = Interpolator((self.x, self.y), 0,
                                                 random_pos, duration, formula=(lambda x: 2. * x - x ** 2))
        else:
            self.pos_interpolator = Interpolator(random_pos, 0,
                                                 (self.x, self.y), duration, formula=(lambda x: 2. * x - x ** 2))
            self.x, self.y = random_pos


    def update(self):
        Effect.update(self)

        self.pos_interpolator.update(self.frame)
        self.x, self.y = self.pos_interpolator.values

        self.frame += 1

