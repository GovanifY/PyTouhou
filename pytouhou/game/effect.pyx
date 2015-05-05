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
from pytouhou.vm import ANMRunner


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
