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

from pytouhou.game.sprite cimport Sprite
from pytouhou.vm.anmrunner import ANMRunner


cdef class Effect(Element):
    def __init__(self, pos, index, anm):
        Element.__init__(self, pos)
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(anm, index, self.sprite)


    cpdef update(self):
        if self.anmrunner is not None and not self.anmrunner.run_frame():
            self.anmrunner = None

        if self.sprite is not None:
            if self.sprite.removed:
                self.sprite = None
                self.removed = True



cdef class Particle(Effect):
    def __init__(self, pos, index, anm, long amp, game, bint reverse=False, long duration=24):
        Effect.__init__(self, pos, index, anm)

        self.frame = 0
        self.duration = duration

        random_pos = (self.x + amp * <double>game.prng.rand_double() - amp / 2,
                      self.y + amp * <double>game.prng.rand_double() - amp / 2)

        if not reverse:
            self.pos_interpolator = Interpolator((self.x, self.y), 0,
                                                 random_pos, duration, formula=(lambda x: 2. * x - x ** 2))
        else:
            self.pos_interpolator = Interpolator(random_pos, 0,
                                                 (self.x, self.y), duration, formula=(lambda x: 2. * x - x ** 2))
            self.x, self.y = random_pos


    cpdef update(self):
        Effect.update(self)

        self.pos_interpolator.update(self.frame)
        self.x, self.y = self.pos_interpolator.values

        self.frame += 1
