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


from pytouhou.utils.random import Random

class GameState(object):
    __slots__ = ('players', 'rank', 'difficulty', 'frame', 'stage', 'boss', 'prng')
    def __init__(self, players, stage, rank, difficulty):
        self.stage = stage
        self.players = players
        self.rank = rank
        self.difficulty = difficulty
        self.boss = None
        self.prng = Random()
        self.frame = 0
