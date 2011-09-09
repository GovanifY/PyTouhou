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

from math import cos, sin, atan2, pi

from pytouhou.utils.interpolator import Interpolator
from pytouhou.vm.anmrunner import ANMRunner
from pytouhou.game.sprite import Sprite


class Bullet(object):
    def __init__(self, pos, type_idx, sprite_idx_offset,
                       angle, speed, attributes, flags, player, game_state):
        self._game_state = game_state
        self._sprite = None
        self._anmrunner = None
        self._removed = False
        self._launched = False
        self._bullet_type = game_state.bullet_types[type_idx]

        self.speed_interpolator = None
        self.frame = 0
        self.grazed = False

        self.player = player

        self.sprite_idx_offset = sprite_idx_offset

        self.flags = flags
        self.attributes = list(attributes)

        self.x, self.y = pos
        self.angle = angle
        self.speed = speed
        dx, dy = cos(angle) * speed, sin(angle) * speed
        self.delta = dx, dy

        #TODO
        if flags & 14:
            bt = self._bullet_type
            if flags & 2:
                index = bt.launch_anim2_index
                launch_mult = bt.launch_anim_penalties[0]
            elif flags & 4:
                index = bt.launch_anim4_index
                launch_mult = bt.launch_anim_penalties[1]
            else:
                index = bt.launch_anim8_index
                launch_mult = bt.launch_anim_penalties[2]
            self.launch_delta = dx * launch_mult, dy * launch_mult
            self._sprite = Sprite()
            self._anmrunner = ANMRunner(bt.anm_wrapper,
                                        index, self._sprite,
                                        bt.launch_anim_offsets[sprite_idx_offset])
            self._anmrunner.run_frame()
        else:
            self.launch()

        self._sprite.angle = angle


    def is_visible(self, screen_width, screen_height):
        tx, ty, tw, th = self._sprite.texcoords
        if self._sprite.corner_relative_placement:
            raise Exception #TODO

        max_x = tw / 2.
        max_y = th / 2.

        if any((max_x < self.x - screen_width,
                max_x < -self.x,
                max_y < self.y - screen_height,
                max_y < -self.y)):
            return False
        return True


    def set_anim(self, sprite_idx_offset=None):
        if sprite_idx_offset is not None:
            self.sprite_idx_offset = sprite_idx_offset

        bt = self._bullet_type
        self._sprite = Sprite()
        self._sprite.angle = self.angle
        self._anmrunner = ANMRunner(bt.anm_wrapper, bt.anim_index,
                                    self._sprite, self.sprite_idx_offset)
        self._anmrunner.run_frame()


    def launch(self):
        self._launched = True
        self.update = self.update_full
        self.set_anim()
        if self.flags & 1:
            self.speed_interpolator = Interpolator((self.speed + 5.,), 0,
                                                   (self.speed,), 16)


    def update(self):
        dx, dy = self.launch_delta
        self.x += dx
        self.y += dy

        self.frame += 1

        if not self._anmrunner.run_frame():
            self.launch()


    def update_simple(self):
        dx, dy = self.delta
        self.x += dx
        self.y += dy


    def update_full(self):
        sprite = self._sprite

        if self._anmrunner is not None and not self._anmrunner.run_frame():
            self._anmrunner = None

        #TODO: flags
        x, y = self.x, self.y
        dx, dy = self.delta

        if self.flags & 16:
            frame, count = self.attributes[0:2]
            length, angle = self.attributes[4:6]
            angle = self.angle if angle < -900.0 else angle #TODO: is that right?
            dx, dy = dx + cos(angle) * length, dy + sin(angle) * length
            self.delta = dx, dy
            if self.frame == frame: #TODO: include last frame, or not?
                if count > 0:
                    self.attributes[1] -= 1
                    self.frame = 0
                else:
                    self.flags ^= 16
        elif self.flags & 32:
            #TODO: check
            frame, count = self.attributes[0:2]
            acceleration, angular_speed = self.attributes[4:6]
            self.speed += acceleration
            self.angle += angular_speed
            dx, dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed
            self.delta = dx, dy
            sprite.angle = self.angle
            if sprite.automatic_orientation:
                sprite._changed = True
            if self.frame % frame == 0:
                if count > 0:
                    self.attributes[1] -= 1
                else:
                    self.flags ^= 32
        elif self.flags & 448:
            #TODO: check
            frame, count = self.attributes[0:2]
            angle, speed = self.attributes[4:6]
            if self.frame % frame == 0:
                count = count - 1

                if self.flags & 64:
                    self.angle += angle
                elif self.flags & 128:
                    self.angle = atan2(self.player.y - y, self.player.x - x) + angle
                elif self.flags & 256:
                    self.angle = angle

                dx, dy = cos(self.angle) * speed, sin(self.angle) * speed
                self.delta = dx, dy
                sprite.angle = self.angle
                if sprite.automatic_orientation:
                    sprite._changed = True

                if count > 0:
                    self.speed_interpolator = Interpolator((speed,), self.frame,
                                                           (0.,), self.frame + frame - 1)
                else:
                    self.flags &= ~448
                    self.speed = speed

                self.attributes[1] = count
        #TODO: other flags
        elif not self.speed_interpolator and self._anmrunner is None:
            self.update = self.update_simple

        if self.speed_interpolator:
            self.speed_interpolator.update(self.frame)
            self.speed, = self.speed_interpolator.values

        self.x, self.y = x + dx, y + dy

        self.frame += 1

