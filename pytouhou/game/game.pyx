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

from pytouhou.vm import MSGRunner

from pytouhou.game.element cimport Element
from pytouhou.game.bullet cimport Bullet, LAUNCHED, CANCELLED
from pytouhou.game.enemy cimport Enemy
from pytouhou.game.item cimport Item
from pytouhou.game.particle cimport Particle
from pytouhou.game.laser cimport Laser, PlayerLaser
from pytouhou.game.face import Face


cdef class Game:
    def __init__(self, players, long stage, long rank, long difficulty, bullet_types,
                 laser_types, item_types, long nb_bullets_max=0, long width=384,
                 long height=448, Random prng=None, interface=None, hints=None,
                 bint friendly_fire=True):
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
        self.texts = {}
        self.interface = interface
        self.hints = hints

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

        self.friendly_fire = friendly_fire
        self.last_keystate = 0


    cdef list msg_sprites(self):
        return [face for face in self.faces if face is not None] if self.msg_runner is not None and not self.msg_runner.ended else []


    cdef list lasers_sprites(self):
        return [laser for laser in self.players_lasers if laser is not None]


    cdef void modify_difficulty(self, long diff) nogil:
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


    cpdef enable_spellcard_effect(self):
        pos = (-32, -16)
        self.spellcard_effect = Effect(pos, 0,
                                       self.spellcard_effect_anm)
        self.spellcard_effect.sprite.allow_dest_offset = True

        face = Effect(pos, 3, self.msg_anm[0][0][0])
        face.sprite.allow_dest_offset = True
        face.sprite.anm, face.sprite.texcoords = self.msg_anm[1][self.spellcard[2]]
        self.effects.append(face)

        self.texts['enemy_spellcard'] = self.new_native_text((384-24, 24), self.spellcard[1], align='right')


    cpdef disable_spellcard_effect(self):
        self.spellcard_effect = None
        if 'enemy_spellcard' in self.texts:
            del self.texts['enemy_spellcard']


    cdef bint set_player_bomb(self) except True:
        face = Effect((-32, -16), 1, self.msg_anm[0][0][0])
        face.sprite.allow_dest_offset = True
        self.effects.append(face)
        self.texts['player_spellcard'] = self.new_native_text((24, 24), u'Player Spellcard')


    cdef bint unset_player_bomb(self) except True:
        del self.texts['player_spellcard']


    cpdef drop_bonus(self, double x, double y, long _type, end_pos=None, player=None):
        if _type > 6:
            return
        if len(self.items) >= self.nb_bullets_max:
            return #TODO: check
        item_type = self.item_types[_type]
        self.items.append(Item((x, y), _type, item_type, self, end_pos=end_pos,
                               player=player))


    cdef bint autocollect(self, Player player) except True:
        cdef Item item

        for item in self.items:
            item.autocollect(player)


    cdef bint cancel_bullets(self) except True:
        cdef Bullet bullet
        cdef Laser laser

        for bullet in self.bullets:
            bullet.cancel()
        for laser in self.lasers:
            laser.cancel()

    cdef bint cancel_player_lasers(self) except True:
        cdef PlayerLaser laser
        for laser in self.players_lasers:
            if laser is not None:
                laser.cancel()


    cpdef change_bullets_into_star_items(self):
        cdef Player player
        cdef Bullet bullet
        cdef Laser laser
        cdef Item item

        player = min(self.players, key=select_player_key)
        item_type = self.item_types[6]
        items = [Item((bullet.x, bullet.y), 6, item_type, self)
                 for bullet in self.bullets]
        for laser in self.lasers:
            items.extend([Item(pos, 6, item_type, self)
                          for pos in laser.get_bullets_pos()])
            laser.cancel()
        for item in items:
            item.autocollect(player)
        self.items.extend(items)
        self.bullets = []


    cpdef change_bullets_into_bonus(self):
        cdef Player player
        cdef Bullet bullet

        score = 0
        bonus = 2000
        for bullet in self.bullets:
            self.new_label((bullet.x, bullet.y), str(bonus).encode())
            score += bonus
            bonus += 10
        self.bullets = []
        #TODO: display the final bonus score.

        #TODO: do we really want to give it to each player?
        for player in self.players:
            player.score += score


    cpdef kill_enemies(self):
        cdef Enemy enemy

        for enemy in self.enemies:
            if enemy.boss:
                pass # Bosses are immune to 96
            elif enemy.touchable:
                enemy.life = 0
            else:
                #TODO: check
                enemy.death_callback.fire()


    cpdef new_effect(self, pos, long anim, anm=None, long number=1):
        number = min(number, self.nb_bullets_max - len(self.effects))
        for i in range(number):
            self.effects.append(Effect(pos, anim, anm or self.etama[1]))


    cpdef new_particle(self, pos, long anim, long amp, long number=1, bint reverse=False, long duration=24):
        number = min(number, self.nb_bullets_max - len(self.effects))
        for i in range(number):
            self.effects.append(Particle(pos, anim, self.etama[1], amp, self, reverse=reverse, duration=duration))


    cpdef new_enemy(self, pos, life, instr_type, bonus_dropped, die_score):
        enemy = Enemy(pos, life, instr_type, bonus_dropped, die_score, self.enm_anm, self)
        self.enemies.append(enemy)
        return enemy


    cpdef new_msg(self, sub):
        self.msg_runner = MSGRunner(self.msg, sub, self)
        self.msg_runner.run_iteration()


    cdef Text new_label(self, tuple pos, bytes text):
        label = Text(pos, self.interface.ascii_anm, text=text, xspacing=8, shift=48)
        label.set_timeout(60, effect='move')
        self.labels.append(label)
        return label


    cpdef NativeText new_native_text(self, tuple pos, unicode text, align='left'):
        label = NativeText(pos, text, shadow=True, align=align)
        return label


    cpdef Text new_hint(self, hint):
        pos = hint['Pos']
        #TODO: Scale

        pos = pos[0] + 192, pos[1]
        label = Text(pos, self.interface.ascii_anm, text=hint['Text'], align=hint['Align'])
        label.set_timeout(hint['Time'])
        label.set_alpha(hint['Alpha'])
        label.set_color(None, hint['Color']) #XXX
        self.labels.append(label)
        return label


    cpdef new_face(self, side, effect):
        face = Face(self.msg_anm, effect, side)
        self.faces[side] = face
        return face


    cpdef run_iter(self, list keystates):
        cdef Laser laser
        cdef long i

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
            self.update_msg(keystates[0]) # Pri ?
            for i in range(len(keystates)):
                keystates[i] &= ~3 # Remove the ability to attack (keystates 1 and 2).
        self.update_players(keystates) # Pri 7
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
        for text in self.texts.values(): #TODO: what priority is it?
            if text is not None:
                text.update()
        self.update_faces() # Pri XXX

        # 5. Clean up
        self.cleanup()

        self.frame += 1


    cdef bint update_background(self) except True:
        if self.time_stop:
            return False
        if self.spellcard_effect is not None:
            self.spellcard_effect.update()
        #TODO: update the actual background here?


    cdef bint update_enemies(self) except True:
        cdef Enemy enemy

        for enemy in self.enemies:
            enemy.update()


    cdef bint update_msg(self, long keystate) except True:
        cdef long k

        for k in (1, 256):
            if keystate & k and not self.last_keystate & k:
                self.msg_runner.skip()
                break
        self.msg_runner.skipping = bool(keystate & 256)
        self.last_keystate = keystate
        self.msg_runner.run_iteration()


    cdef bint update_players(self, list keystates) except True:
        cdef Bullet bullet
        cdef Player player
        cdef long keystate

        if self.time_stop:
            return False

        for bullet in self.players_bullets:
            bullet.update()

        for player, keystate in zip(self.players, keystates):
            player.update(keystate) #TODO: differentiate keystates (multiplayer mode)

            old_effective_score = player.effective_score
            #XXX: Why 78910? Is it really the right value?
            player.effective_score = min(old_effective_score + 78910,
                                         player.score)
            if self.stage < 7:
                for i in [10000000, 20000000, 40000000, 60000000]:
                    if player.effective_score >= i and old_effective_score < i:
                        if player.lives < 8:
                            player.lives += 1
                        self.modify_difficulty(+2)
                        player.play_sound('extend')


    cdef bint update_effects(self) except True:
        cdef Element effect

        for effect in self.effects:
            effect.update()


    cdef bint update_hints(self) except True:
        for hint in self.hints:
            if hint['Count'] == self.frame and hint['Base'] == 'start':
                self.new_hint(hint)


    cdef bint update_faces(self) except True:
        for face in self.faces:
            if face:
                face.update()


    cdef bint update_bullets(self) except True:
        cdef Player player
        cdef Bullet bullet
        cdef Item item
        cdef PlayerLaser player_laser
        cdef Laser laser
        cdef PlayerLaser plaser
        cdef double player_pos[2]

        if self.time_stop:
            return False

        for bullet in self.cancelled_bullets:
            bullet.update()

        for bullet in self.bullets:
            bullet.update()

        for player_laser in self.players_lasers:
            if player_laser is not None:
                player_laser.update()

        for item in self.items:
            item.update()

        for player in self.players:
            if not player.touchable:
                continue

            px, py = player.x, player.y
            player_pos[:] = [px, py]
            phalf_size = <double>player.sht.hitbox
            px1, px2 = px - phalf_size, px + phalf_size
            py1, py2 = py - phalf_size, py + phalf_size

            ghalf_size = <double>player.sht.graze_hitbox
            gx1, gx2 = px - ghalf_size, px + ghalf_size
            gy1, gy2 = py - ghalf_size, py + ghalf_size

            for laser in self.lasers:
                if laser.check_collision(player_pos):
                    if player.invulnerable_time == 0:
                        player.collide()
                elif laser.check_grazing(player_pos):
                    player.graze += 1 #TODO
                    player.score += 500 #TODO
                    player.play_sound('graze')
                    self.modify_difficulty(+6) #TODO
                    self.new_particle((px, py), 9, 192) #TODO

            for bullet in self.bullets:
                if bullet.state != LAUNCHED:
                    continue

                bhalf_width = bullet.hitbox[0]
                bhalf_height = bullet.hitbox[1]
                bx, by = bullet.x, bullet.y
                bx1, bx2 = bx - bhalf_width, bx + bhalf_width
                by1, by2 = by - bhalf_height, by + bhalf_height

                if not (bx2 < px1 or bx1 > px2
                        or by2 < py1 or by1 > py2):
                    bullet.collide()
                    if player.invulnerable_time == 0:
                        player.collide()

                elif not bullet.grazed and not (bx2 < gx1 or bx1 > gx2
                        or by2 < gy1 or by1 > gy2):
                    bullet.grazed = True
                    player.graze += 1
                    player.score += 500 # found experimentally
                    player.play_sound('graze')
                    self.modify_difficulty(+6)
                    self.new_particle((px, py), 9, 192) #TODO: find the real size and range.
                    #TODO: display a static particle during one frame at
                    # 12 pixels of the player, in the axis of the “collision”.

            # Check for friendly-fire only if there are multiple players.
            if self.friendly_fire and len(self.players) > 1:
                for bullet in self.players_bullets:
                    if bullet.state != LAUNCHED:
                        continue

                    if bullet.player == player.number:
                        continue

                    bhalf_width = bullet.hitbox[0]
                    bhalf_height = bullet.hitbox[1]
                    bx, by = bullet.x, bullet.y
                    bx1, bx2 = bx - bhalf_width, bx + bhalf_width
                    by1, by2 = by - bhalf_height, by + bhalf_height

                    if not (bx2 < px1 or bx1 > px2
                            or by2 < py1 or by1 > py2):
                        bullet.collide()
                        if player.invulnerable_time == 0:
                            player.collide()

                for plaser in self.players_lasers:
                    if not plaser:
                        continue

                    lhalf_width = plaser.hitbox[0]
                    lx, ly = plaser.x, plaser.y * 2.
                    lx1, lx2 = lx - lhalf_width, lx + lhalf_width

                    if not (lx2 < px1 or lx1 > px2
                            or ly < py1):
                        if player.invulnerable_time == 0:
                            player.collide()

            #TODO: is it the right place?
            if py < 128 and player.power >= 128: #TODO: check py.
                self.autocollect(player)

            ihalf_size = <double>player.sht.item_hitbox
            for item in self.items:
                bx, by = item.x, item.y
                bx1, bx2 = bx - ihalf_size, bx + ihalf_size
                by1, by2 = by - ihalf_size, by + ihalf_size

                if not (bx2 < px1 or bx1 > px2
                        or by2 < py1 or by1 > py2):
                    item.on_collect(player)


    cpdef cleanup(self):
        cdef Enemy enemy
        cdef Bullet bullet
        cdef Item item
        cdef PlayerLaser laser
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
        self.texts = {key: text for key, text in self.texts.items() if not text.removed}

        # Disable boss mode if it is dead/it has timeout
        if self.boss and self.boss.removed:
            self.boss = None


cdef list filter_removed(list elements):
    cdef Element element

    filtered = []
    for element in elements:
        if not element.removed:
            filtered.append(element)
    return filtered


def select_player_key(player):
    return (player.score, player.character)
