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
from pytouhou.game.effect import Effect
from pytouhou.game.effect import Particle



class Game(object):
    def __init__(self, resource_loader, player_states, stage, rank, difficulty,
                 bullet_types, item_types, characters, prng=None, nb_bullets_max=None):
        self.resource_loader = resource_loader

        self.nb_bullets_max = nb_bullets_max
        self.bullet_types = bullet_types
        self.item_types = item_types
        self.characters = characters

        self.players = [Player(player_state, characters[player_state.character], self) for player_state in player_states]
        self.enemies = []
        self.effects = []
        self.bullets = []
        self.cancelled_bullets = []
        self.players_bullets = []
        self.items = []

        self.stage = stage
        self.rank = rank
        self.difficulty = difficulty
        self.boss = None
        self.spellcard = None
        self.deaths_count = 0
        self.next_bonus = 0
        self.bonus_list = [0,0,1,0,1,0,0,1,1,1,0,0,0,1,1,0,1,0,1,0,1,0,1,0,1,0,0,1,1,1,0,2]
        self.prng = prng or Random()
        self.frame = 0

        self.enm_anm_wrapper = resource_loader.get_anm_wrapper2(('stg%denm.anm' % stage,
                                                                 'stg%denm2.anm' % stage))
        self.etama4 = resource_loader.get_anm_wrapper(('etama4.anm',))
        ecl = resource_loader.get_ecl('ecldata%d.ecl' % stage)
        self.ecl_runner = ECLMainRunner(ecl, self)

        #TODO: The game calls it two times. What for?
        # See 102h.exe@0x413220 if you think you're brave enough.
        self.prng.rand_uint16()
        self.prng.rand_uint16()


    def drop_bonus(self, x, y, _type, end_pos=None):
        player = self.players[0] #TODO
        if _type > 6:
            return
        item_type = self.item_types[_type]
        item = Item((x, y), item_type, self, end_pos=end_pos)
        self.items.append(item)


    def change_bullets_into_star_items(self):
        player = self.players[0] #TODO
        item_type = self.item_types[6]
        self.items.extend(Item((bullet.x, bullet.y), item_type, self, player=player) for bullet in self.bullets)
        self.bullets = []


    def new_death(self, pos, index):
        anim = {0: 3, 1: 4, 2: 5}[index % 256] # The TB is wanted, if index isn’t in these values the original game crashs.
        self.effects.append(Effect(pos, anim, self.etama4))


    def new_particle(self, pos, color, size, amp, delay=False):
        self.effects.append(Particle(pos, 7 + 4 * color + self.prng.rand_uint16() % 4, self.etama4, size, amp, delay, self))


    def new_enemy(self, pos, life, instr_type, bonus_dropped, die_score):
        enemy = Enemy(pos, life, instr_type, bonus_dropped, die_score, self.enm_anm_wrapper, self)
        self.enemies.append(enemy)
        return enemy


    def run_iter(self, keystate):
        # 1. VMs.
        self.ecl_runner.run_iter()

        # 2. Filter out destroyed enemies
        self.enemies = [enemy for enemy in self.enemies if not enemy._removed]
        self.effects = [enemy for enemy in self.effects if not enemy._removed]
        self.bullets = [bullet for bullet in self.bullets if not bullet._removed]
        self.cancelled_bullets = [bullet for bullet in self.cancelled_bullets if not bullet._removed]
        self.items = [item for item in self.items if not item._removed]

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

        for enemy in self.effects:
            enemy.update()

        for bullet in self.bullets:
            bullet.update()

        for bullet in self.cancelled_bullets:
            bullet.update()

        for bullet in self.players_bullets:
            bullet.update()

        for item in self.items:
            item.update()

        # 4. Check for collisions!
        #TODO
        for player in self.players:
            if not player.state.touchable:
                continue

            px, py = player.x, player.y
            phalf_size = player.hitbox_half_size
            px1, px2 = px - phalf_size, px + phalf_size
            py1, py2 = py - phalf_size, py + phalf_size

            ghalf_size = player.graze_hitbox_half_size
            gx1, gx2 = px - ghalf_size, px + ghalf_size
            gy1, gy2 = py - ghalf_size, py + ghalf_size

            for bullet in self.bullets:
                half_size = bullet.hitbox_half_size
                bx, by = bullet.x, bullet.y
                bx1, bx2 = bx - half_size, bx + half_size
                by1, by2 = by - half_size, by + half_size

                if not (bx2 < px1 or bx1 > px2
                        or by2 < py1 or by1 > py2):
                    bullet.collide()
                    if player.state.invulnerable_time == 0:
                        player.collide()

                elif not bullet.grazed and not (bx2 < gx1 or bx1 > gx2
                        or by2 < gy1 or by1 > gy2):
                    bullet.grazed = True
                    player.state.graze += 1
                    player.state.score += 500 # found experimentally
                    self.new_particle((px, py), 0, .8, 192, delay=True) #TODO: find the real size and range.
                    #TODO: display a static particle during one frame at
                    # 12 pixels of the player, in the axis of the “collision”.

            for enemy in self.enemies:
                half_size_x, half_size_y = enemy.hitbox_half_size
                bx, by = enemy.x, enemy.y
                bx1, bx2 = bx - half_size_x, bx + half_size_x
                by1, by2 = by - half_size_y, by + half_size_y

                if enemy.touchable and not (bx2 < px1 or bx1 > px2
                                            or by2 < py1 or by1 > py2):
                    enemy.on_collide()
                    if player.state.invulnerable_time == 0:
                        player.collide()

            for item in self.items:
                half_size = item.hitbox_half_size
                bx, by = item.x, item.y
                bx1, bx2 = bx - half_size, bx + half_size
                by1, by2 = by - half_size, by + half_size

                if not (bx2 < px1 or bx1 > px2
                        or by2 < py1 or by1 > py2):
                    player.collect(item)

        for enemy in self.enemies:
            ex, ey = enemy.x, enemy.y
            ehalf_size_x, ehalf_size_y = enemy.hitbox_half_size
            ex1, ex2 = ex - ehalf_size_x, ex + ehalf_size_x
            ey1, ey2 = ey - ehalf_size_y, ey + ehalf_size_y

            for bullet in self.players_bullets:
                half_size = bullet.hitbox_half_size
                bx, by = bullet.x, bullet.y
                bx1, bx2 = bx - half_size, bx + half_size
                by1, by2 = by - half_size, by + half_size

                if not (bx2 < ex1 or bx1 > ex2
                        or by2 < ey1 or by1 > ey2):
                    bullet.collide()
                    enemy.on_attack(bullet)
                    player.state.score += 90 # found experimentally

        # 5. Cleaning
        self.cleanup()

        self.frame += 1


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
        self.bullets = [bullet for bullet in self.bullets if bullet.is_visible(384, 448)]
        self.cancelled_bullets = [bullet for bullet in self.cancelled_bullets if bullet.is_visible(384, 448)]
        self.players_bullets = [bullet for bullet in self.players_bullets if bullet.is_visible(384, 448)]

        # Filter out-of-scren items
        self.items = [item for item in self.items if item.y < 448]

        # Disable boss mode if it is dead/it has timeout
        if self.boss and self.boss._removed:
            self.boss = None

