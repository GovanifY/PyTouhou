# -*- encoding: utf-8 -*-
##
## Copyright (C) 2011 Thibaut Girka <thib@sitedethib.com>
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


from math import cos, sin, atan2, pi

from pytouhou.game.sprite import Sprite
from pytouhou.vm.anmrunner import ANMRunner


SQ2 = 2. ** 0.5 / 2.


class PlayerState(object):
    def __init__(self, character=0, score=0, power=0, lives=0, bombs=0):
        self.character = character # ReimuA/ReimuB/MarisaA/MarisaB/...

        self.score = score
        self.lives = lives
        self.bombs = bombs
        self.power = power

        self.graze = 0
        self.points = 0

        self.x = 192.0
        self.y = 384.0


class Player(object):
    def __init__(self, state, character):
        self._sprite = None
        self._anmrunner = None

        self.state = state
        self.character = character
        self.anm_wrapper = character.anm_wrapper
        self.direction = None

        self.set_anim(0)


    @property
    def x(self):
        return self.state.x


    @property
    def y(self):
        return self.state.y


    def set_anim(self, index):
        self._sprite = Sprite()
        self._anmrunner = ANMRunner(self.anm_wrapper, index, self._sprite)
        self._anmrunner.run_frame()


    def update(self, keystate):
        try:
            dx, dy = {16: (0.0, -1.0), 32: (0.0, 1.0), 64: (-1.0, 0.0), 128: (1.0, 0.0),
                      16|64: (-SQ2, -SQ2), 16|128: (SQ2, -SQ2),
                      32|64: (-SQ2, SQ2), 32|128:  (SQ2, SQ2)}[keystate & (16|32|64|128)]
        except KeyError:
            speed = 0.0
            dx, dy = 0.0, 0.0
        else:
            speed = self.character.focused_speed if keystate & 4 else self.character.speed
            dx, dy = dx * speed, dy * speed

        if dx < 0 and self.direction != -1:
            self.set_anim(1)
            self.direction = -1
        elif dx > 0 and self.direction != +1:
            self.set_anim(3)
            self.direction = +1
        elif dx == 0 and self.direction is not None:
            self.set_anim({-1: 2, +1: 4}[self.direction])
            self.direction = None

        self.state.x += dx
        self.state.y += dy

        self._anmrunner.run_frame()

