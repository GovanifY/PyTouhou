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

from pytouhou.vm.eclrunner import ECLMainRunner

from pytouhou.game.enemy import Enemy


class GameState(object):
    __slots__ = ('resource_loader', 'bullets', 'players', 'rank', 'difficulty', 'frame',
                 'stage', 'boss', 'prng', 'bullet_types')
    def __init__(self, resource_loader, players, stage, rank, difficulty, bullet_types):
        self.resource_loader = resource_loader

        self.bullet_types = bullet_types

        self.bullets = []

        self.stage = stage
        self.players = players
        self.rank = rank
        self.difficulty = difficulty
        self.boss = None
        self.prng = Random()
        self.frame = 0



class Game(object):
    def __init__(self, resource_loader, players, stage, rank, difficulty, bullet_types):
        self.game_state = GameState(resource_loader, players, stage, rank, difficulty, bullet_types)

        self.enemies = []

        self.bonuses = []

        self.enm_anm_wrapper = resource_loader.get_anm_wrapper2(('stg%denm.anm' % stage,
                                                                 'stg%denm2.anm' % stage))
        ecl = resource_loader.get_ecl('ecldata%d.ecl' % stage)
        self.ecl_runner = ECLMainRunner(ecl, self.new_enemy, self.game_state)


    def new_enemy(self, pos, life, instr_type):
        enemy = Enemy(pos, life, instr_type, self.enm_anm_wrapper, self.game_state)
        self.enemies.append(enemy)
        return enemy


    def run_iter(self, keystate):
        # 1. VMs.
        self.ecl_runner.run_iter()

        # 2. Filter out destroyed enemies
        self.enemies = [enemy for enemy in self.enemies if not enemy._removed]

        # 3. Let's play!
        for enemy in self.enemies:
            enemy.update()

        for bullet in self.game_state.bullets:
            bullet.update()

        # 4. Cleaning
        self.cleanup()

        self.game_state.frame += 1


    def cleanup(self):
        # Filter out non-visible enemies
        for enemy in tuple(self.enemies):
            if enemy.is_visible(384, 448): #TODO
                enemy._was_visible = True
            elif enemy._was_visible:
                # Filter out-of-screen enemy
                enemy._removed = True
                self.enemies.remove(enemy)

        # Filter out-of-scren bullets
        # TODO: was_visible thing
        self.game_state.bullets = [bullet for bullet in self.game_state.bullets if bullet.is_visible(384, 448)]

        # Disable boss mode if it is dead/it has timeout
        if self.game_state.boss and self.game_state.boss._removed:
            self.game_state.boss = None

