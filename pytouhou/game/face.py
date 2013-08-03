# -*- encoding: utf-8 -*-
##
## Copyright (C) 2012 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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


class Face(object):
    __slots__ = ('_anms', 'sprite', 'anmrunner', 'side', 'x', 'y', 'objects')

    def __init__(self, anms, effect, side):
        self._anms = anms
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(self._anms[0][0][0], side * 2, self.sprite)
        self.side = side
        self.load(0)
        self.animate(effect)
        self.objects = [self]

        #FIXME: the same as game.effect.
        self.x = -32
        self.y = -16
        self.sprite.allow_dest_offset = True


    def animate(self, effect):
        self.anmrunner.interrupt(effect)


    def load(self, index):
        self.sprite.anm, self.sprite.texcoords = self._anms[self.side][index]
        self.anmrunner.run_frame()


    def update(self):
        self.anmrunner.run_frame()
