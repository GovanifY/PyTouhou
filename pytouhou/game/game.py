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

from itertools import chain

from pytouhou.vm.eclrunner import ECLMainRunner
from pytouhou.vm.msgrunner import MSGRunner

from pytouhou.game.bullet import LAUNCHED, CANCELLED
from pytouhou.game.enemy import Enemy
from pytouhou.game.item import Item
from pytouhou.game.effect import Effect
from pytouhou.game.effect import Particle
from pytouhou.game.text import Text



class GameOver(Exception):
    pass


class Game(object):
    def __init__(self, resource_loader, players, stage, rank, difficulty,
                 bullet_types, laser_types, item_types,
                 nb_bullets_max=None, width=384, height=448, prng=None,
                 interface=None, continues=0):
        self.resource_loader = resource_loader

        self.width, self.height = width, height

        self.nb_bullets_max = nb_bullets_max
        self.bullet_types = bullet_types
        self.laser_types = laser_types
        self.item_types = item_types

        self.players = players
        self.enemies = []
        self.effects = []
        self.bullets = []
        self.lasers = []
        self.cancelled_bullets = []
        self.players_bullets = []
        self.players_lasers = [None, None]
        self.items = []
        self.labels = []
        self.interface = interface

        self.continues = continues
        self.stage = stage
        self.rank = rank
        self.difficulty = difficulty
        self.difficulty_counter = 0
        self.difficulty_min = 12 if rank == 0 else 10
        self.difficulty_max = 20 if rank == 0 else 32
        self.boss = None
        self.spellcard = None
        self.time_stop = False
        self.msg_runner = None
        self.msg_wait = False
        self.bonus_list = [0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0,
                           1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 2]
        self.prng = prng
        self.frame = 0

        self.enm_anm_wrapper = resource_loader.get_anm_wrapper2(('stg%denm.anm' % stage,
                                                                 'stg%denm2.anm' % stage))
        self.etama4 = resource_loader.get_anm_wrapper(('etama4.anm',))
        ecl = resource_loader.get_ecl('ecldata%d.ecl' % stage)
        self.ecl_runners = [ECLMainRunner(main, ecl.subs, self) for main in ecl.mains]

        self.spellcard_effect_anm_wrapper = resource_loader.get_anm_wrapper(('eff0%d.anm' % stage,))
        self.spellcard_effect = None

        #TODO: better place?
        self.ascii_wrapper = resource_loader.get_anm_wrapper(('ascii.anm',))

        # See 102h.exe@0x413220 if you think you're brave enough.
        self.deaths_count = self.prng.rand_uint16() % 3
        self.next_bonus = self.prng.rand_uint16() % 8

        self.last_keystate = 0


    def msg_sprites(self):
        return []


    def lasers_sprites(self):
        return [laser for laser in self.players_lasers if laser]


    def modify_difficulty(self, diff):
        self.difficulty_counter += diff
        while self.difficulty_counter < 0:
            self.difficulty -= 1
            self.difficulty_counter += 100
        while self.difficulty_counter >= 100:
            self.difficulty += 1
            self.difficulty_counter -= 100
        if self.difficulty < self.difficulty_min:
            self.difficulty = self.difficulty_min
        elif self.difficulty > self.difficulty_max:
            self.difficulty = self.difficulty_max


    def enable_spellcard_effect(self):
        self.spellcard_effect = Effect((-32., -16.), 0,
                                       self.spellcard_effect_anm_wrapper) #TODO: find why this offset is necessary.
        self.spellcard_effect.sprite.allow_dest_offset = True #TODO: should be the role of anm’s 25th instruction. Investigate!


    def disable_spellcard_effect(self):
        self.spellcard_effect = None


    def drop_bonus(self, x, y, _type, end_pos=None):
        player = self.players[0] #TODO
        if _type > 6:
            return
        if len(self.items) >= self.nb_bullets_max:
            return #TODO: check
        item_type = self.item_types[_type]
        item = Item((x, y), _type, item_type, self, end_pos=end_pos)
        self.items.append(item)


    def autocollect(self, player):
        for item in self.items:
            if not item.player:
                item.autocollect(player)


    def cancel_bullets(self):
        for bullet in self.bullets:
            bullet.cancel()
        for laser in self.lasers:
            laser.cancel()


    def change_bullets_into_star_items(self):
        player = self.players[0] #TODO
        item_type = self.item_types[6]
        self.items.extend(Item((bullet.x, bullet.y), 6, item_type, self, player=player)
                            for bullet in self.bullets)
        for laser in self.lasers:
            self.items.extend(Item(pos, 6, item_type, self, player=player)
                                for pos in laser.get_bullets_pos())
            laser.cancel()
        self.bullets = []


    def change_bullets_into_bonus(self):
        player = self.players[0] #TODO
        score = 0
        bonus = 2000
        for bullet in self.bullets:
            label = self.new_label((bullet.x, bullet.y), str(bonus))
            score += bonus
            bonus += 10
        self.bullets = []
        player.state.score += score
        #TODO: display the final bonus score.


    def kill_enemies(self):
        for enemy in self.enemies:
            if enemy.boss:
                pass # Bosses are immune to 96
            elif enemy.touchable:
                enemy.life = 0
            elif enemy.death_callback > 0:
                #TODO: check
                enemy.process.switch_to_sub(enemy.death_callback)
                enemy.death_callback = -1


    def new_effect(self, pos, anim, anm_wrapper=None):
        self.effects.append(Effect(pos, anim, anm_wrapper or self.etama4))


    def new_particle(self, pos, color, size, amp):
        self.effects.append(Particle(pos, 7 + 4 * color + self.prng.rand_uint16() % 4, self.etama4, size, amp, self))


    def new_enemy(self, pos, life, instr_type, bonus_dropped, die_score):
        enemy = Enemy(pos, life, instr_type, bonus_dropped, die_score, self.enm_anm_wrapper, self)
        self.enemies.append(enemy)
        return enemy


    def new_msg(self, sub):
        self.msg_runner = MSGRunner(self.msg, sub, self)
        self.msg_runner.run_iteration()


    def new_label(self, pos, text):
        label = Text(pos, self.ascii_wrapper, text=text, xspacing=8, shift=48)
        label.set_timeout(60)
        self.labels.append(label)
        return label


    def run_iter(self, keystate):
        # 1. VMs.
        for runner in self.ecl_runners:
            runner.run_iter()

        # 2. Modify difficulty
        if self.frame % (32*60) == (32*60): #TODO: check if that is really that frame.
            self.modify_difficulty(+100)

        # 3. Filter out destroyed enemies
        self.enemies = [enemy for enemy in self.enemies if not enemy.removed]
        self.effects = [effect for effect in self.effects if not effect.removed]
        self.bullets = [bullet for bullet in self.bullets if not bullet.removed]
        self.cancelled_bullets = [bullet for bullet in self.cancelled_bullets if not bullet.removed]
        self.items = [item for item in self.items if not item.removed]


        # 4. Let's play!
        # In the original game, updates are done in prioritized functions called "chains"
        # We have to mimic this functionnality to be replay-compatible with the official game.

        # Pri 6 is background
        self.update_background() #TODO: Pri unknown
        if self.msg_runner:
            self.update_msg(keystate) # Pri ?
            keystate &= ~3 # Remove the ability to attack (keystates 1 and 2).
        self.update_players(keystate) # Pri 7
        self.update_enemies() # Pri 9
        self.update_effects() # Pri 10
        self.update_bullets() # Pri 11
        for laser in self.lasers: #TODO: what priority is it?
            laser.update()
        self.interface.update() # Pri 12
        for label in self.labels: #TODO: what priority is it?
            label.update()

        # 5. Clean up
        self.cleanup()

        self.frame += 1


    def update_background(self):
        if self.time_stop:
            return None
        if self.spellcard_effect is not None:
            self.spellcard_effect.update()
        #TODO: update the actual background here?


    def update_enemies(self):
        for enemy in self.enemies:
            enemy.update()


    def update_msg(self, keystate):
        if any((keystate & k and not self.last_keystate & k) for k in (1, 256)):
            self.msg_runner.skip()
        self.msg_runner.skipping = bool(keystate & 256)
        self.last_keystate = keystate
        self.msg_runner.run_iteration()


    def update_players(self, keystate):
        if self.time_stop:
            return None

        for bullet in self.players_bullets:
            bullet.update()

        for player in self.players:
            player.update(keystate) #TODO: differentiate keystates (multiplayer mode)

        #XXX: Why 78910? Is it really the right value?
        player.state.effective_score = min(player.state.effective_score + 78910,
                                           player.state.score)
        #TODO: give extra lives to the player


    def update_effects(self):
        for effect in self.effects:
            effect.update()


    def update_bullets(self):
        if self.time_stop:
            return None
        for bullet in self.cancelled_bullets:
            bullet.update()

        for bullet in self.bullets:
            bullet.update()

        for laser in self.players_lasers:
            if laser:
                laser.update()

        for item in self.items:
            item.update()

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

            for laser in self.lasers:
                if laser.check_collision((px, py)):
                    if player.state.invulnerable_time == 0:
                        player.collide()
                elif laser.check_grazing((px, py)):
                    player.state.graze += 1 #TODO
                    player.state.score += 500 #TODO
                    player.play_sound('graze')
                    self.modify_difficulty(+6) #TODO
                    self.new_particle((px, py), 0, .8, 192) #TODO

            for bullet in self.bullets:
                if bullet.state != LAUNCHED:
                    continue

                half_size = bullet.hitbox_half_size
                bx, by = bullet.x, bullet.y
                bx1, bx2 = bx - half_size[0], bx + half_size[0]
                by1, by2 = by - half_size[1], by + half_size[1]

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
                    player.play_sound('graze')
                    self.modify_difficulty(+6)
                    self.new_particle((px, py), 0, .8, 192) #TODO: find the real size and range.
                    #TODO: display a static particle during one frame at
                    # 12 pixels of the player, in the axis of the “collision”.

            #TODO: is it the right place?
            if py < 128 and player.state.power >= 128: #TODO: check py.
                self.autocollect(player)

            half_size = player.sht.item_hitbox / 2.
            for item in self.items:
                bx, by = item.x, item.y
                bx1, bx2 = bx - half_size, bx + half_size
                by1, by2 = by - half_size, by + half_size

                if not (bx2 < px1 or bx1 > px2
                        or by2 < py1 or by1 > py2):
                    item.on_collect(player)


    def cleanup(self):
        # Filter out non-visible enemies
        for enemy in self.enemies:
            if enemy.is_visible(self.width, self.height):
                enemy.was_visible = True
            elif enemy.was_visible:
                # Filter out-of-screen enemy
                enemy.removed = True

        self.enemies = [enemy for enemy in self.enemies if not enemy.removed]

        # Update cancelled bullets
        self.cancelled_bullets = [b for b in chain(self.cancelled_bullets,
                                                   self.bullets,
                                                   self.players_bullets)
                                    if b.state == CANCELLED and not b.removed]
        # Filter out-of-scren bullets
        self.bullets = [bullet for bullet in self.bullets
                            if not bullet.removed and bullet.state != CANCELLED]
        self.players_bullets = [bullet for bullet in self.players_bullets
                            if not bullet.removed and bullet.state != CANCELLED]
        for i, laser in enumerate(self.players_lasers):
            if laser and laser.removed:
                self.players_lasers[i] = None
        self.effects = [effect for effect in self.effects if not effect.removed]

        # Filter “timed-out” lasers
        self.lasers = [laser for laser in self.lasers if not laser.removed]

        # Filter out-of-scren items
        items = []
        for item in self.items:
            if item.y < self.height:
                items.append(item)
            else:
                self.modify_difficulty(-3)
        self.items = items

        self.labels = [label for label in self.labels if not label.removed]

        # Disable boss mode if it is dead/it has timeout
        if self.boss and self.boss._enemy.removed:
            self.boss = None

