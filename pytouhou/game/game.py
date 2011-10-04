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

from pytouhou.game.player import Player
from pytouhou.game.enemy import Enemy
from pytouhou.game.item import Item


class GameState(object):
    __slots__ = ('resource_loader', 'bullets', 'items', 'players', 'rank', 'difficulty', 'frame',
                 'stage', 'boss', 'prng', 'bullet_types', 'item_types', 'characters', 'nb_bullets_max')
    def __init__(self, resource_loader, players, stage, rank, difficulty,
                 bullet_types, item_types, characters, nb_bullets_max):
        self.resource_loader = resource_loader

        self.bullet_types = bullet_types
        self.item_types = item_types
        self.characters = characters

        self.bullets = []
        self.items = []
        self.nb_bullets_max = nb_bullets_max

        self.stage = stage
        self.players = players
        self.rank = rank
        self.difficulty = difficulty
        self.boss = None
        self.prng = Random()
        self.frame = 0


    def change_bullets_into_star_items(self):
        player = self.players[0] #TODO
        item_type = self.item_types[6]
        self.items.extend(Item((bullet.x, bullet.y), item_type, 0.0, item_type.speed, player, self) for bullet in self.bullets)
        self.bullets = []



class Game(object):
    def __init__(self, resource_loader, player_states, stage, rank, difficulty,
                 bullet_types, item_types, characters, nb_bullets_max=None):
        self.game_state = GameState(resource_loader, player_states, stage,
                                    rank, difficulty,
                                    bullet_types, item_types, characters, nb_bullets_max)

        self.players = [Player(player_state, characters[player_state.character]) for player_state in player_states]
        self.enemies = []

        self.bonuses = []

        self.enm_anm_wrapper = resource_loader.get_anm_wrapper2(('stg%denm.anm' % stage,
                                                                 'stg%denm2.anm' % stage))
        ecl = resource_loader.get_ecl('ecldata%d.ecl' % stage)
        self.ecl_runner = ECLMainRunner(ecl, self.new_enemy, self.game_state)


    def new_enemy(self, pos, life, instr_type, pop_enemy):
        enemy = Enemy(pos, life, instr_type, self.enm_anm_wrapper, self.game_state, pop_enemy)
        self.enemies.append(enemy)
        return enemy


    def run_iter(self, keystate):
        # 1. VMs.
        self.ecl_runner.run_iter()

        # 2. Filter out destroyed enemies
        self.enemies = [enemy for enemy in self.enemies if not enemy._removed]

        # 3. Let's play!
        #TODO: check update orders
        for player in self.players:
            player.update(keystate) #TODO: differentiate keystates (multiplayer mode)
            if player.state.x < 8.:
                player.state.x = 8.
            if player.state.x > 384.-8: #TODO
                player.state.x = 384.-8
            if player.state.y < 16.:
                player.state.y = 16.
            if player.state.y > 448.-16: #TODO
                player.state.y = 448.-16

        for enemy in self.enemies:
            enemy.update()

        for bullet in self.game_state.bullets:
            bullet.update()

        for item in self.game_state.items:
            item.update()

        # 4. Check for collisions!
        #TODO
        for player in self.players:
            px, py = player.x, player.y
            phalf_size = player.hitbox_half_size
            px1, px2 = px - phalf_size, px + phalf_size
            py1, py2 = py - phalf_size, py + phalf_size
            for bullet in self.game_state.bullets:
                half_size = bullet.hitbox_half_size
                bx, by = bullet.x, bullet.y
                bx1, bx2 = bx - half_size, bx + half_size
                by1, by2 = by - half_size, by + half_size

                if not (bx2 < px1 or bx1 > px2
                        or by2 < py1 or by1 > py2):
                    print('collided!') #TODO

        #TODO: enemy-player collision
        #TODO: item-player collision

        # 5. Cleaning
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

