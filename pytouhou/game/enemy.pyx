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

from libc.math cimport cos, sin, atan2, M_PI as pi

from pytouhou.vm import ANMRunner
from pytouhou.game.sprite import Sprite
from pytouhou.game.bullet cimport Bullet, LAUNCHED
from pytouhou.game.laser cimport Laser, PlayerLaser
from pytouhou.game.effect cimport Effect


cdef class Callback:
    def __init__(self, function=None, args=()):
        self.function = function
        self.args = args

    def __nonzero__(self):
        return self.function is not None

    cpdef enable(self, function, tuple args):
        self.function = function
        self.args = args

    cpdef disable(self):
        self.function = None

    cpdef fire(self):
        if self.function is not None:
            self.function(*self.args)
            self.function = None


cdef class Enemy(Element):
    def __init__(self, pos, long life, long _type, long bonus_dropped, long die_score, anms, Game game):
        Element.__init__(self)

        self._game = game
        self._anms = anms
        self._type = _type

        self.process = None
        self.visible = True
        self.was_visible = False
        self.bonus_dropped = bonus_dropped
        self.die_score = die_score

        self.frame = 0

        self.x, self.y, self.z = pos
        self.life = 1 if life < 0 else life
        self.touchable = True
        self.collidable = True
        self.damageable = True
        self.death_flags = 0
        self.boss = False
        self.difficulty_coeffs = (-.5, .5, 0, 0, 0, 0)
        self.extended_bullet_attributes = (0, 0, 0, 0, 0., 0., 0., 0.)
        self.current_laser_id = 0
        self.laser_by_id = {}
        self.bullet_attributes = None
        self.bullet_launch_offset = (0, 0)
        self.low_life_trigger = -1
        self.timeout = -1
        self.remaining_lives = 0

        self.death_callback = Callback()
        self.boss_callback = Callback()
        self.low_life_callback = Callback()
        self.timeout_callback = Callback()

        self.automatic_orientation = False

        self.bullet_launch_interval = 0
        self.bullet_launch_timer = 0
        self.delay_attack = False

        self.death_anim = 0
        self.movement_dependant_sprites = None
        self.direction = 0
        self.interpolator = None #TODO
        self.speed_interpolator = None
        self.update_mode = 0
        self.angle = 0.
        self.speed = 0.
        self.rotation_speed = 0.
        self.acceleration = 0.

        self.hitbox_half_size[:] = [0, 0]
        self.screen_box = None

        self.aux_anm = 8 * [None]


    property objects:
        def __get__(self):
            return [self] + [anm for anm in self.aux_anm if anm is not None]


    cpdef play_sound(self, index):
        name = {
            5: 'power0',
            6: 'power1',
            7: 'tan00',
            8: 'tan01',
            9: 'tan02',
            14: 'cat00',
            16: 'lazer00',
            17: 'lazer01',
            18: 'enep01',
            22: 'tan00', #XXX
            24: 'tan02', #XXX
            25: 'kira00',
            26: 'kira01',
            27: 'kira02'
        }[index]
        self._game.sfx_player.play('%s.wav' % name)


    cpdef set_hitbox(self, double width, double height):
        self.hitbox_half_size[:] = [width / 2, height / 2]


    cpdef set_bullet_attributes(self, type_, anim, sprite_idx_offset,
                                unsigned long bullets_per_shot,
                                unsigned long number_of_shots, double speed,
                                double speed2, launch_angle, angle, flags):
        cdef double speed_a, speed_b
        cdef long nb_a, nb_b, shots_a, shots_b

        # Apply difficulty-specific modifiers
        speed_a, speed_b, nb_a, nb_b, shots_a, shots_b = self.difficulty_coeffs
        diff_coeff = self._game.difficulty / 32.

        speed += speed_a * (1. - diff_coeff) + speed_b * diff_coeff
        speed2 += (speed_a * (1. - diff_coeff) + speed_b * diff_coeff) / 2.
        bullets_per_shot += <long>(nb_a * (1. - diff_coeff) + nb_b * diff_coeff)
        number_of_shots += <long>(shots_a * (1. - diff_coeff) + shots_b * diff_coeff)

        self.bullet_attributes = (type_, anim, sprite_idx_offset, bullets_per_shot,
                                  number_of_shots, speed, speed2, launch_angle,
                                  angle, flags)
        if not self.delay_attack:
            self.fire()


    cpdef set_bullet_launch_interval(self, long value, unsigned long start=0):
        # Apply difficulty-specific modifiers:
        #TODO: check every value possible! Look around 102h.exe@0x408720
        value -= value * (self._game.difficulty - 16) // 80

        self.bullet_launch_interval = value
        self.bullet_launch_timer = start % value if value > 0 else 0


    cpdef fire(self, offset=None, bullet_attributes=None, tuple launch_pos=None):
        cdef unsigned long type_, bullets_per_shot, number_of_shots
        cdef double speed, speed2, launch_angle, angle

        (type_, type_idx, sprite_idx_offset, bullets_per_shot, number_of_shots,
         speed, speed2, launch_angle, angle, flags) = bullet_attributes or self.bullet_attributes

        bullet_type = self._game.bullet_types[type_idx]

        if launch_pos is None:
            ox, oy = offset or self.bullet_launch_offset
            launch_pos = self.x + ox, self.y + oy

        if speed < 0.3 and speed != 0.0:
            speed = 0.3
        if speed2 < 0.3:
            speed2 = 0.3

        self.bullet_launch_timer = 0

        player = self.select_player()

        if type_ in (67, 69, 71):
            launch_angle += self.get_angle(player, launch_pos)
        if type_ == 71 and bullets_per_shot % 2 or type_ in (69, 70) and not bullets_per_shot % 2:
            launch_angle += pi / bullets_per_shot
        if type_ != 75:
            launch_angle -= angle * (bullets_per_shot - 1) / 2.

        bullets = self._game.bullets
        nb_bullets_max = self._game.nb_bullets_max

        for shot_nb in range(number_of_shots):
            shot_speed = speed if shot_nb == 0 else speed + (speed2 - speed) * float(shot_nb) / float(number_of_shots)
            bullet_angle = launch_angle
            if type_ in (69, 70, 71, 74):
                launch_angle += angle
            for bullet_nb in range(bullets_per_shot):
                if nb_bullets_max is not None and len(bullets) == nb_bullets_max:
                    break

                if type_ == 75: # 102h.exe@0x4138cf
                    bullet_angle = self._game.prng.rand_double() * (launch_angle - angle) + angle
                if type_ in (74, 75): # 102h.exe@0x4138cf
                    shot_speed = self._game.prng.rand_double() * (speed - speed2) + speed2
                bullets.append(Bullet(launch_pos, bullet_type, sprite_idx_offset,
                                      bullet_angle, shot_speed,
                                      self.extended_bullet_attributes,
                                      flags, player, self._game))

                if type_ in (69, 70, 71, 74):
                    bullet_angle += 2. * pi / bullets_per_shot
                else:
                    bullet_angle += angle


    cpdef new_laser(self, unsigned long variant, laser_type, sprite_idx_offset,
                    double angle, speed, start_offset, end_offset, max_length,
                    width, start_duration, duration, end_duration,
                    grazing_delay, grazing_extra_duration, unknown,
                    tuple offset=None):
        cdef double ox, oy

        if offset is None:
            offset = self.bullet_launch_offset
        ox, oy = offset
        launch_pos = self.x + ox, self.y + oy
        if variant == 86:
            player = self.select_player()
            angle += self.get_angle(player, launch_pos)
        laser = Laser(launch_pos, self._game.laser_types[laser_type],
                      sprite_idx_offset, angle, speed,
                      start_offset, end_offset, max_length, width,
                      start_duration, duration, end_duration, grazing_delay,
                      grazing_extra_duration, self._game)
        self._game.lasers.append(laser)
        self.laser_by_id[self.current_laser_id] = laser


    cpdef Player select_player(self, list players=None):
        if players is None:
            players = self._game.players
        return min(players, key=self.select_player_key)


    cpdef double get_angle(self, Element target, tuple pos=None) except 42:
        cdef double x, y
        x, y = pos or (self.x, self.y)
        return atan2(target.y - y, target.x - x)


    cpdef set_anim(self, index):
        entry = 0 if index in self._anms[0].scripts else 1
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(self._anms[entry], index, self.sprite)


    cdef bint die_anim(self) except True:
        anim = {0: 3, 1: 4, 2: 5}[self.death_anim % 256] # The TB is wanted, if index isn’t in these values the original game crashs.
        self._game.new_effect((self.x, self.y), anim)
        self._game.sfx_player.play('enep00.wav')


    cdef bint drop_particles(self, long number, long color) except True:
        if color == 0:
            if self._game.stage in [1, 2, 7]:
                color = 3
        color += 9
        for i in range(number):
            self._game.new_particle((self.x, self.y), color, 256) #TODO: find the real size.


    cpdef set_aux_anm(self, long number, long index):
        entry = 0 if index in self._anms[0].scripts else 1
        self.aux_anm[number] = Effect((self.x, self.y), index, self._anms[entry])


    cpdef set_pos(self, double x, double y, double z):
        self.x, self.y = x, y
        self.update_mode = 1
        self.interpolator = Interpolator((x, y), self._game.frame)


    cpdef move_to(self, unsigned long duration, double x, double y, double z,
                  formula):
        frame = self._game.frame
        self.speed_interpolator = None
        self.update_mode = 1
        self.interpolator = Interpolator((self.x, self.y), frame,
                                         (x, y), frame + duration - 1,
                                         formula)

        self.angle = atan2(y - self.y, x - self.x)


    cpdef stop_in(self, unsigned long duration, formula):
        frame = self._game.frame
        self.interpolator = None
        self.update_mode = 1
        self.speed_interpolator = Interpolator((self.speed,), frame,
                                               (0.,), frame + duration - 1,
                                               formula)


    cpdef set_boss(self, bint enable):
        if enable:
            self.boss = True
            self._game.boss = self
            self._game.interface.set_boss_life()
        else:
            self.boss = False
            self._game.boss = None


    cdef bint is_visible(self, long screen_width, long screen_height) except -1:
        if self.sprite is not None:
            if self.sprite.corner_relative_placement:
                raise Exception #TODO
            tw, th = self.sprite._texcoords[2], self.sprite._texcoords[3]
        else:
            tw, th = 0., 0.

        x, y = self.x, self.y
        max_x = tw / 2
        max_y = th / 2

        if (max_x < x - screen_width
            or max_x < -x
            or max_y < y - screen_height
            or max_y < -y):
            return False
        return True


    cdef bint check_collisions(self) except True:
        cdef Bullet bullet
        cdef Player player
        cdef PlayerLaser laser
        cdef long damages
        cdef double half_size[2]
        cdef double phalf_size

        # Check for collisions
        ex, ey = self.x, self.y
        ehalf_size_x = self.hitbox_half_size[0]
        ehalf_size_y = self.hitbox_half_size[1]
        ex1, ex2 = ex - ehalf_size_x, ex + ehalf_size_x
        ey1, ey2 = ey - ehalf_size_y, ey + ehalf_size_y

        damages = 0

        # Check for enemy-bullet collisions
        for bullet in self._game.players_bullets:
            if bullet.state != LAUNCHED:
                continue
            half_size[0] = bullet.hitbox[0]
            half_size[1] = bullet.hitbox[1]
            bx, by = bullet.x, bullet.y
            bx1, bx2 = bx - half_size[0], bx + half_size[0]
            by1, by2 = by - half_size[1], by + half_size[1]

            if not (bx2 < ex1 or bx1 > ex2
                    or by2 < ey1 or by1 > ey2):
                bullet.collide()
                damages += bullet.damage
                self._game.sfx_player.play('damage00.wav')

        # Check for enemy-laser collisions
        for laser in self._game.players_lasers:
            if not laser:
                continue

            half_size[0] = laser.hitbox[0]
            lx, ly = laser.x, laser.y * 2.
            lx1, lx2 = lx - half_size[0], lx + half_size[0]

            if not (lx2 < ex1 or lx1 > ex2
                    or ly < ey1):
                damages += laser.damage
                self._game.sfx_player.play('damage00.wav')
                self.drop_particles(1, 1) #TODO: don’t call each frame.

        # Check for enemy-player collisions
        ex1, ex2 = ex - ehalf_size_x * 2. / 3., ex + ehalf_size_x * 2. / 3.
        ey1, ey2 = ey - ehalf_size_y * 2. / 3., ey + ehalf_size_y * 2. / 3.
        if self.collidable:
            for player in self._game.players:
                px, py = player.x, player.y
                phalf_size = player.sht.hitbox
                px1, px2 = px - phalf_size, px + phalf_size
                py1, py2 = py - phalf_size, py + phalf_size

                #TODO: box-box or point-in-box?
                if not (ex2 < px1 or ex1 > px2 or ey2 < py1 or ey1 > py2):
                    if not self.boss:
                        damages += 10
                    player.collide()

        # Adjust damages
        damages = min(70, damages)
        score = (damages // 5) * 10
        self._game.players[0].score += score #TODO: better distribution amongst the players.

        if self.damageable:
            if self._game.spellcard is not None:
                #TODO: there is a division by 3, somewhere... where is it?
                if damages <= 7:
                    damages = 1 if damages else 0
                else:
                    damages //= 7

            nb_players = len(self._game.players)
            if nb_players > 1:
                if damages <= nb_players:
                    damages = 1 if damages else 0
                else:
                    damages //= nb_players

            # Apply damages
            self.life -= damages


    cdef bint handle_callbacks(self) except True:
        #TODO: implement missing callbacks and clean up!
        if self.life <= 0 and self.touchable:
            self.timeout = -1 #TODO: not really true, the timeout is frozen
            self.timeout_callback.disable()
            death_flags = self.death_flags & 7

            self.die_anim()

            #TODO: verify if the score is added with all the different flags.
            self._game.players[0].score += self.die_score #TODO: better distribution amongst the players.

            #TODO: verify if that should really be there.
            if self.boss:
                self._game.change_bullets_into_bonus()

            if death_flags < 4:
                if self.bonus_dropped > -1:
                    self.drop_particles(7, 0)
                    self._game.drop_bonus(self.x, self.y, self.bonus_dropped)
                elif self.bonus_dropped == -1:
                    if self._game.deaths_count % 3 == 0:
                        self.drop_particles(10, 0)
                        self._game.drop_bonus(self.x, self.y, self._game.bonus_list[self._game.next_bonus])
                        self._game.next_bonus = (self._game.next_bonus + 1) % 32
                    else:
                        self.drop_particles(4, 0)
                    self._game.deaths_count += 1
                else:
                    self.drop_particles(4, 0)

                if death_flags == 0:
                    self.removed = True
                    return False

                if death_flags == 1:
                    if self.boss:
                        self.boss = False #TODO: really?
                        self._game.boss = None
                    self.touchable = False
                elif death_flags == 2:
                    pass # Just that?
                elif death_flags == 3:
                    if self.boss:
                        self.boss = False #TODO: really?
                        self._game.boss = None
                    self.damageable = False
                    self.life = 1
                    self.death_flags = 0

            if death_flags != 0:
                self.death_callback.fire()
        elif self.life <= self.low_life_trigger and self.low_life_callback:
            self.low_life_callback.fire()
            self.low_life_trigger = -1
            self.timeout_callback.disable()
        elif self.timeout != -1 and self.frame == self.timeout:
            self.frame = 0
            self.timeout = -1
            self._game.kill_enemies()
            self._game.cancel_bullets()

            if self.low_life_trigger > 0:
                self.life = self.low_life_trigger
                self.low_life_trigger = -1

            if self.timeout_callback:
                self.timeout_callback.fire()
            #TODO: this is only done under certain (unknown) conditions!
            # but it shouldn't hurt anyway, as the only option left is to crash!
            elif self.death_callback:
                self.life = 0 #TODO: do this next frame? Bypass self.touchable?
            else:
                raise Exception('What the hell, man!')


    cdef bint update(self) except True:
        cdef double x, y, speed

        if self.process is not None:
            self.process.run_iteration()

        x, y = self.x, self.y

        if self.update_mode == 1:
            speed = 0.
            if self.interpolator:
                self.interpolator.update(self._game.frame)
                x, y = self.interpolator.values
            if self.speed_interpolator:
                self.speed_interpolator.update(self._game.frame)
                speed, = self.speed_interpolator.values
        else:
            speed = self.speed
            self.speed += self.acceleration
            self.angle += self.rotation_speed

        dx, dy = cos(self.angle) * speed, sin(self.angle) * speed
        if self._type & 2:
            x -= dx
        else:
            x += dx
        y += dy

        if self.movement_dependant_sprites is not None:
            #TODO: is that really how it works? Almost.
            # Sprite determination is done only once per changement, and is
            # superseeded by ins_97.
            end_left, end_right, left, right = self.movement_dependant_sprites
            if x < self.x and self.direction != -1:
                self.set_anim(left)
                self.direction = -1
            elif x > self.x and self.direction != +1:
                self.set_anim(right)
                self.direction = +1
            elif x == self.x and self.direction != 0:
                self.set_anim({-1: end_left, +1: end_right}[self.direction])
                self.direction = 0


        if self.screen_box is not None:
            xmin, ymin, xmax, ymax = self.screen_box
            x = max(xmin, min(x, xmax))
            y = max(ymin, min(y, ymax))


        self.x, self.y = x, y

        #TODO
        if self.anmrunner is not None and not self.anmrunner.run_frame():
            self.anmrunner = None

        if self.sprite is not None and self.visible:
            if self.sprite.removed:
                self.sprite = None
            else:
                self.sprite.update_orientation(self.angle,
                                               self.automatic_orientation)


        if self.bullet_launch_interval != 0:
            self.bullet_launch_timer += 1
            if self.bullet_launch_timer == self.bullet_launch_interval:
                self.fire()

        # Check collisions
        if self.touchable:
            self.check_collisions()

        for anm in self.aux_anm:
            if anm is not None:
                anm.x, anm.y = self.x, self.y
                anm.update()

        self.handle_callbacks()

        self.frame += 1


    def select_player_key(self, player):
        return ((player.x - self.x) ** 2 + (player.y - self.y) ** 2, player.character)
