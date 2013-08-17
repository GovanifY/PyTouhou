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

from pytouhou.vm.msgrunner import MSGRunner

from pytouhou.game.element cimport Element
from pytouhou.game.bullet cimport Bullet
from pytouhou.game.bullet import LAUNCHED, CANCELLED
from pytouhou.game.enemy cimport Enemy
from pytouhou.game.item cimport Item
from pytouhou.game.effect cimport Particle
from pytouhou.game.text import Text
from pytouhou.game.face import Face


cdef class Game:
    def __init__(self, players, long stage, long rank, long difficulty, bullet_types,
                 laser_types, item_types, long nb_bullets_max=0, long width=384,
                 long height=448, prng=None, interface=None, double continues=0,
                 hints=None):
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
        self.faces = [None, None]
        self.interface = interface
        self.hints = hints

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
        self.sfx_player = None

        self.spellcard_effect = None

        # See 102h.exe@0x413220 if you think you're brave enough.
        self.deaths_count = self.prng.rand_uint16() % 3
        self.next_bonus = self.prng.rand_uint16() % 8

        self.last_keystate = 0


    def msg_sprites(self):
        return [face for face in self.faces if face is not None] if self.msg_runner is not None and not self.msg_runner.ended else []


    def lasers_sprites(self):
        return [laser for laser in self.players_lasers if laser is not None]


    cpdef modify_difficulty(self, long diff):
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
                                       self.spellcard_effect_anm) #TODO: find why this offset is necessary.
        self.spellcard_effect.sprite.allow_dest_offset = True #TODO: should be the role of anm’s 25th instruction. Investigate!


    def disable_spellcard_effect(self):
        self.spellcard_effect = None


    cpdef drop_bonus(self, double x, double y, long _type, end_pos=None):
        if _type > 6:
            return
        if len(self.items) >= self.nb_bullets_max:
            return #TODO: check
        item_type = self.item_types[_type]
        self.items.append(Item((x, y), _type, item_type, self, end_pos=end_pos))


    cdef void autocollect(self, Player player):
        cdef Item item

        for item in self.items:
            item.autocollect(player)


    cpdef cancel_bullets(self):
        cdef Bullet bullet
        #TODO: cdef Laser laser

        for bullet in self.bullets:
            bullet.cancel()
        for laser in self.lasers:
            laser.cancel()


    def change_bullets_into_star_items(self):
        cdef Player player
        cdef Bullet bullet

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
        cdef Player player
        cdef Bullet bullet

        player = self.players[0] #TODO
        score = 0
        bonus = 2000
        for bullet in self.bullets:
            self.new_label((bullet.x, bullet.y), str(bonus))
            score += bonus
            bonus += 10
        self.bullets = []
        player.state.score += score
        #TODO: display the final bonus score.


    def kill_enemies(self):
        cdef Enemy enemy

        for enemy in self.enemies:
            if enemy.boss:
                pass # Bosses are immune to 96
            elif enemy.touchable:
                enemy.life = 0
            elif enemy.death_callback > 0:
                #TODO: check
                enemy.process.switch_to_sub(enemy.death_callback)
                enemy.death_callback = -1


    def new_effect(self, pos, long anim, anm=None, long number=1):
        number = min(number, self.nb_bullets_max - len(self.effects))
        for i in xrange(number):
            self.effects.append(Effect(pos, anim, anm or self.etama[1]))


    cpdef new_particle(self, pos, long anim, long amp, long number=1, bint reverse=False, long duration=24):
        number = min(number, self.nb_bullets_max - len(self.effects))
        for i in xrange(number):
            self.effects.append(Particle(pos, anim, self.etama[1], amp, self, reverse=reverse, duration=duration))


    def new_enemy(self, pos, life, instr_type, bonus_dropped, die_score):
        enemy = Enemy(pos, life, instr_type, bonus_dropped, die_score, self.enm_anm, self)
        self.enemies.append(enemy)
        return enemy


    def new_msg(self, sub):
        self.msg_runner = MSGRunner(self.msg, sub, self)
        self.msg_runner.run_iteration()


    cpdef new_label(self, pos, str text):
        label = Text(pos, self.interface.ascii_anm, text=text, xspacing=8, shift=48)
        label.set_timeout(60, effect='move')
        self.labels.append(label)
        return label


    def new_hint(self, hint):
        pos = hint['Pos']
        #TODO: Scale

        pos = pos[0] + 192, pos[1]
        label = Text(pos, self.interface.ascii_anm, text=hint['Text'], align=hint['Align'])
        label.set_timeout(hint['Time'])
        label.set_alpha(hint['Alpha'])
        label.set_color(hint['Color'], text=False)
        self.labels.append(label)
        return label


    def new_face(self, side, effect):
        face = Face(self.msg_anm, effect, side)
        self.faces[side] = face
        return face


    def run_iter(self, long keystate):
        # 1. VMs.
        for runner in self.ecl_runners:
            runner.run_iter()

        # 2. Modify difficulty
        if self.frame % (32*60) == (32*60): #TODO: check if that is really that frame.
            self.modify_difficulty(+100)

        # 3. Filter out destroyed enemies
        self.enemies = filter_removed(self.enemies)
        self.effects = filter_removed(self.effects)
        self.bullets = filter_removed(self.bullets)
        self.cancelled_bullets = filter_removed(self.cancelled_bullets)
        self.items = filter_removed(self.items)

        # 4. Let's play!
        # In the original game, updates are done in prioritized functions called "chains"
        # We have to mimic this functionnality to be replay-compatible with the official game.

        # Pri 6 is background
        self.update_background() #TODO: Pri unknown
        if self.msg_runner is not None:
            self.update_msg(keystate) # Pri ?
            keystate &= ~3 # Remove the ability to attack (keystates 1 and 2).
        self.update_players(keystate) # Pri 7
        self.update_enemies() # Pri 9
        self.update_effects() # Pri 10
        self.update_bullets() # Pri 11
        for laser in self.lasers: #TODO: what priority is it?
            laser.update()
        self.interface.update() # Pri 12
        if self.hints:
            self.update_hints() # Not from this game, so unknown.
        for label in self.labels: #TODO: what priority is it?
            label.update()
        self.update_faces() # Pri XXX

        # 5. Clean up
        self.cleanup()

        self.frame += 1


    cdef void update_background(self):
        if self.time_stop:
            return
        if self.spellcard_effect is not None:
            self.spellcard_effect.update()
        #TODO: update the actual background here?


    cdef void update_enemies(self):
        cdef Enemy enemy

        for enemy in self.enemies:
            enemy.update()


    cdef void update_msg(self, long keystate) except *:
        cdef long k

        if any([(keystate & k and not self.last_keystate & k) for k in (1, 256)]):
            self.msg_runner.skip()
        self.msg_runner.skipping = bool(keystate & 256)
        self.last_keystate = keystate
        self.msg_runner.run_iteration()


    cdef void update_players(self, long keystate) except *:
        cdef Bullet bullet
        cdef Player player

        if self.time_stop:
            return

        for bullet in self.players_bullets:
            bullet.update()

        for player in self.players:
            player.update(keystate) #TODO: differentiate keystates (multiplayer mode)

        #XXX: Why 78910? Is it really the right value?
        player.state.effective_score = min(player.state.effective_score + 78910,
                                           player.state.score)
        #TODO: give extra lives to the player


    cdef void update_effects(self):
        cdef Element effect

        for effect in self.effects:
            effect.update()


    cdef void update_hints(self):
        for hint in self.hints:
            if hint['Count'] == self.frame and hint['Base'] == 'start':
                self.new_hint(hint)


    cdef void update_faces(self):
        for face in self.faces:
            if face:
                face.update()


    cdef void update_bullets(self):
        cdef Player player
        cdef Bullet bullet
        cdef Item item
        cdef double bhalf_width, bhalf_height

        if self.time_stop:
            return

        for bullet in self.cancelled_bullets:
            bullet.update()

        for bullet in self.bullets:
            bullet.update()

        for laser in self.players_lasers:
            if laser is not None:
                laser.update()

        for item in self.items:
            item.update()

        for player in self.players:
            player_state = player.state

            if not player_state.touchable:
                continue

            px, py = player_state.x, player_state.y
            phalf_size = <double>player.sht.hitbox
            px1, px2 = px - phalf_size, px + phalf_size
            py1, py2 = py - phalf_size, py + phalf_size

            ghalf_size = <double>player.sht.graze_hitbox
            gx1, gx2 = px - ghalf_size, px + ghalf_size
            gy1, gy2 = py - ghalf_size, py + ghalf_size

            for laser in self.lasers:
                if laser.check_collision((px, py)):
                    if player_state.invulnerable_time == 0:
                        player.collide()
                elif laser.check_grazing((px, py)):
                    player_state.graze += 1 #TODO
                    player_state.score += 500 #TODO
                    player.play_sound('graze')
                    self.modify_difficulty(+6) #TODO
                    self.new_particle((px, py), 9, 192) #TODO

            for bullet in self.bullets:
                if bullet.state != LAUNCHED:
                    continue

                bhalf_width, bhalf_height = bullet.hitbox
                bx, by = bullet.x, bullet.y
                bx1, bx2 = bx - bhalf_width, bx + bhalf_width
                by1, by2 = by - bhalf_height, by + bhalf_height

                if not (bx2 < px1 or bx1 > px2
                        or by2 < py1 or by1 > py2):
                    bullet.collide()
                    if player_state.invulnerable_time == 0:
                        player.collide()

                elif not bullet.grazed and not (bx2 < gx1 or bx1 > gx2
                        or by2 < gy1 or by1 > gy2):
                    bullet.grazed = True
                    player_state.graze += 1
                    player_state.score += 500 # found experimentally
                    player.play_sound('graze')
                    self.modify_difficulty(+6)
                    self.new_particle((px, py), 9, 192) #TODO: find the real size and range.
                    #TODO: display a static particle during one frame at
                    # 12 pixels of the player, in the axis of the “collision”.

            #TODO: is it the right place?
            if py < 128 and player_state.power >= 128: #TODO: check py.
                self.autocollect(player)

            ihalf_size = <double>player.sht.item_hitbox
            for item in self.items:
                bx, by = item.x, item.y
                bx1, bx2 = bx - ihalf_size, bx + ihalf_size
                by1, by2 = by - ihalf_size, by + ihalf_size

                if not (bx2 < px1 or bx1 > px2
                        or by2 < py1 or by1 > py2):
                    item.on_collect(player)


    cdef void cleanup(self):
        cdef Enemy enemy
        cdef Bullet bullet
        cdef Item item
        cdef long i

        # Filter out non-visible enemies
        for enemy in self.enemies:
            if enemy.is_visible(self.width, self.height):
                enemy.was_visible = True
            elif enemy.was_visible:
                # Filter out-of-screen enemy
                enemy.removed = True

        self.enemies = filter_removed(self.enemies)

        # Filter out-of-scren bullets
        cancelled_bullets = []
        bullets = []
        players_bullets = []

        for bullet in self.cancelled_bullets:
            if bullet.state == CANCELLED and not bullet.removed:
                cancelled_bullets.append(bullet)

        for bullet in self.bullets:
            if not bullet.removed:
                if bullet.state == CANCELLED:
                    cancelled_bullets.append(bullet)
                else:
                    bullets.append(bullet)

        for bullet in self.players_bullets:
            if not bullet.removed:
                if bullet.state == CANCELLED:
                    cancelled_bullets.append(bullet)
                else:
                    players_bullets.append(bullet)

        self.cancelled_bullets = cancelled_bullets
        self.bullets = bullets
        self.players_bullets = players_bullets

        # Filter “timed-out” lasers
        for i, laser in enumerate(self.players_lasers):
            if laser is not None and laser.removed:
                self.players_lasers[i] = None

        self.lasers = filter_removed(self.lasers)

        # Filter out-of-scren items
        items = []
        for item in self.items:
            if item.y < self.height:
                items.append(item)
            else:
                self.modify_difficulty(-3)
        self.items = items

        self.effects = filter_removed(self.effects)
        self.labels = filter_removed(self.labels)

        # Disable boss mode if it is dead/it has timeout
        if self.boss and self.boss._enemy.removed:
            self.boss = None

cdef list filter_removed(list elements):
    cdef Element element

    filtered = []
    for element in elements:
        if not element.removed:
            filtered.append(element)
    return filtered
