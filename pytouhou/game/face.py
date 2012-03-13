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
    __slots__ = ('_anm_wrapper', 'sprite', 'anmrunner', 'side', 'x', 'y')

    def __init__(self, anm_wrapper, effect, side):
        self._anm_wrapper = anm_wrapper
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(anm_wrapper, side * 2, self.sprite)
        self.side = side
        self.load(0)
        self.animate(effect)

        #FIXME: the same as game.effect.
        self.x = -32
        self.y = -16
        self.sprite.allow_dest_offset = True


    def animate(self, effect):
        self.anmrunner.interrupt(effect)


    def load(self, index):
        self.sprite.anm, self.sprite.texcoords = self._anm_wrapper.get_sprite(self.side * 8 + index)
        self.anmrunner.run_frame()


    def update(self):
        self.anmrunner.run_frame()

