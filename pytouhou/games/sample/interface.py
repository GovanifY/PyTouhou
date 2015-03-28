# -*- encoding: utf-8 -*-
##
## Copyright (C) 2014 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

class Interface:
    width = 384
    height = 448
    game_pos = (0, 0)

    def __init__(self, resource_loader, player_state):
        self.game = None
        self.player_state = player_state
        self.ascii_anm = resource_loader.get_single_anm('ascii.anm') #XXX

        self.items = []
        self.level_start = []
        self.labels = {}
        self.boss_items = []


    def start_stage(self, game, stage):
        self.game = game


    def set_song_name(self, name):
        pass


    def set_boss_life(self):
        pass


    def set_spell_life(self):
        pass


    def update(self):
        pass
