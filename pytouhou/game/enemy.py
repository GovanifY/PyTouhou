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
from io import BytesIO
import os
from struct import unpack, pack
from pytouhou.utils.interpolator import Interpolator
from pytouhou.vm.eclrunner import ECLRunner
from pytouhou.vm.anmrunner import ANMRunner
from pytouhou.game.sprite import Sprite
from pytouhou.game.bullet import Bullet
from math import cos, sin, atan2, pi


class Enemy(object):
    def __init__(self, pos, life, _type, anm_wrapper, game_state):
        self._game_state = game_state
        self._anm_wrapper = anm_wrapper
        self._sprite = None
        self._anmrunner = None
        self._removed = False
        self._type = _type
        self._was_visible = False

        self.frame = 0

        self.x, self.y = pos
        self.life = life
        self.max_life = life
        self.touchable = True
        self.damageable = True
        self.death_flags = 0
        self.bullets = []
        self.extended_bullet_attributes = (0, 0, 0, 0, 0., 0., 0., 0.)
        self.bullet_attributes = None
        self.bullet_launch_offset = (0, 0)
        self.death_callback = None
        self.low_life_callback = None
        self.low_life_trigger = None
        self.timeout = None
        self.timeout_callback = None
        self.remaining_lives = -1

        self.automatic_orientation = False

        self.bullet_launch_interval = 0
        self.bullet_launch_timer = 0
        self.delay_attack = False

        self.death_anim = None
        self.movement_dependant_sprites = None
        self.direction = None
        self.interpolator = None #TODO
        self.speed_interpolator = None
        self.angle = 0.
        self.speed = 0.
        self.rotation_speed = 0.
        self.acceleration = 0.

        self.hitbox = (0, 0)
        self.screen_box = None


    def set_bullet_attributes(self, type_, anim, sprite_idx_offset,
                              bullets_per_shot, number_of_shots, speed, speed2,
                              launch_angle, angle, flags):
        self.bullet_attributes = (type_, anim, sprite_idx_offset, bullets_per_shot,
                                  number_of_shots, speed, speed2, launch_angle,
                                  angle, flags)
        if not self.delay_attack:
            self.fire()


    def fire(self):
        (type_, anim, sprite_idx_offset, bullets_per_shot, number_of_shots,
         speed, speed2, launch_angle, angle, flags) = self.bullet_attributes

        self.bullet_launch_timer = 0

        player = self.select_player()

        if type_ in (67, 69, 71):
            launch_angle += self.get_player_angle(player)
        if type_ in (69, 70, 71):
            angle = 2. * pi / bullets_per_shot
        if type_ == 71:
            launch_angle += pi / bullets_per_shot

        launch_angle -= angle * (bullets_per_shot - 1) / 2.

        for shot_nb in range(number_of_shots):
            shot_speed = speed if shot_nb == 0 else speed + (speed2 - speed) * float(shot_nb) / float(number_of_shots)
            bullet_angle = launch_angle
            for bullet_nb in range(bullets_per_shot):
                self.bullets.append(Bullet((self.x, self.y),
                                           anim, sprite_idx_offset,
                                           bullet_angle, shot_speed,
                                           self.extended_bullet_attributes,
                                           flags, player, self._game_state))
                bullet_angle += angle


    def select_player(self, players=None):
        return (players or self._game_state.players)[0] #TODO


    def get_player_angle(self, player=None):
        player = player or self.select_player()
        return atan2(player.y - self.y, player.x - self.x)


    def set_anim(self, index):
        self._sprite = Sprite()
        self._anmrunner = ANMRunner(self._anm_wrapper, index, self._sprite)


    def set_pos(self, x, y, z):
        self.x, self.y = x, y
        self.interpolator = Interpolator((x, y))
        self.interpolator.set_interpolation_start(self.frame, (x, y))


    def move_to(self, duration, x, y, z, formula):
        if not self.interpolator:
            self.interpolator = Interpolator((self.x, self.y), formula)
            self.interpolator.set_interpolation_start(self.frame, (self.x, self.y))
            self.interpolator.set_interpolation_end(self.frame + duration - 1, (x, y))

            self.speed = 0.
            self.angle = atan2(y - self.y, x - self.x)


    def stop_in(self, duration, formula):
        if not self.speed_interpolator:
            self.speed_interpolator = Interpolator((self.speed,), formula)
            self.speed_interpolator.set_interpolation_start(self.frame, (self.speed,))
            self.speed_interpolator.set_interpolation_end(self.frame + duration - 1, (0.,))

            self.speed = 0.


    def is_visible(self, screen_width, screen_height):
        if self._sprite:
            tx, ty, tw, th = self._sprite.texcoords
            if self._sprite.corner_relative_placement:
                raise Exception #TODO
        else:
            tx, ty, tw, th = 0., 0., 0., 0.

        max_x = tw / 2.
        max_y = th / 2.
        min_x = -max_x
        min_y = -max_y

        if any((min_x > screen_width - self.x,
                max_x < -self.x,
                min_y > screen_height - self.y,
                max_y < -self.y)):
            return False
        return True


    def get_objects_by_texture(self, objects_by_texture):
        for bullet in self.bullets:
            bullet.get_objects_by_texture(objects_by_texture)

        if not self._sprite:
            return

        sprite = self._sprite
        sprite.update_vertices_uvs_colors()

        key = sprite.anm.first_name, sprite.anm.secondary_name
        key = (key, sprite.blendfunc)
        rec = objects_by_texture.setdefault(key, ([], [], []))
        vertices = ((x + self.x, y + self.y, z) for x, y, z in sprite._vertices)
        rec[0].extend(vertices)
        rec[1].extend(sprite._uvs)
        rec[2].extend(sprite._colors)


    def update(self):
        x, y = self.x, self.y
        if self.interpolator:
            self.interpolator.update(self.frame)
            x, y = self.interpolator.values

        self.speed += self.acceleration #TODO: units? Execution order?
        self.angle += self.rotation_speed #TODO: units? Execution order?


        if self.speed_interpolator:
            self.speed_interpolator.update(self.frame)
            self.speed, = self.speed_interpolator.values


        dx, dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed
        if self._type & 2:
            x -= dx
        else:
            x += dx
        y += dy

        if self.movement_dependant_sprites:
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
            elif x == self.x and self.direction is not None:
                self.set_anim({-1: end_left, +1: end_right}[self.direction])
                self.direction = None


        if self.screen_box:
            xmin, ymin, xmax, ymax = self.screen_box
            x = max(xmin, min(x, xmax))
            y = max(ymin, min(y, ymax))


        self.x, self.y = x, y

        #TODO
        if self._anmrunner and not self._anmrunner.run_frame():
            self._anmrunner = None

        if self._sprite:
            if self._sprite._removed:
                self._sprite = None
            else:
                self._sprite.update(angle_base=self.angle,
                                    force_rotation=self.automatic_orientation)


        if self.bullet_launch_interval != 0:
            self.bullet_launch_timer += 1
            if self.bullet_launch_timer == self.bullet_launch_interval:
                self.fire()


        for bullet in self.bullets:
            bullet.update()


        self.frame += 1

