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


from pytouhou.game.element import Element
from pytouhou.game.sprite import Sprite
from pytouhou.vm import ANMRunner


class Face(Element):
    __slots__ = ('_anms', 'side')

    def __init__(self, anms, effect, side):
        Element.__init__(self, (-32, -16))

        self._anms = anms
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(self._anms[0][0][0], side * 2, self.sprite)
        self.side = side
        self.load(0)
        self.animate(effect)

        #FIXME: the same as game.effect.
        self.sprite.allow_dest_offset = True


    def animate(self, effect):
        self.anmrunner.interrupt(effect)


    def load(self, index):
        self.sprite.anm, self.sprite.texcoords = self._anms[self.side][index]


    def update(self):
        self.anmrunner.run_frame()
