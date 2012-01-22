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


LAUNCHING, LAUNCHED, CANCELLED = range(3)

cdef class Bullet(object):
    cdef public unsigned int _state, flags, frame, sprite_idx_offset
    cdef public double dx, dy, angle, speed #TODO
    cdef public object player_bullet, target
    cdef public object _game, _sprite, _anmrunner, _removed, _bullet_type, _was_visible
    cdef public object attributes, damage, hitbox_half_size, speed_interpolator, grazed
    cdef public object x, y #TODO

    def __init__(self, pos, bullet_type, sprite_idx_offset,
                       angle, speed, attributes, flags, target, game,
                       player_bullet=False, damage=0, hitbox=None):
        self._game = game
        self._sprite = None
        self._anmrunner = None
        self._removed = False
        self._bullet_type = bullet_type
        self._was_visible = True
        self._state = LAUNCHING

        if hitbox:
            self.hitbox_half_size = (hitbox[0] / 2., hitbox[1] / 2.)
        else:
            self.hitbox_half_size = (bullet_type.hitbox_size / 2., bullet_type.hitbox_size / 2.)

        self.speed_interpolator = None
        self.frame = 0
        self.grazed = False

        self.target = target

        self.sprite_idx_offset = sprite_idx_offset

        self.flags = flags
        self.attributes = list(attributes)

        self.x, self.y = pos
        self.angle = angle
        self.speed = speed
        self.dx, self.dy = cos(angle) * speed, sin(angle) * speed

        self.player_bullet = player_bullet
        self.damage = damage

        #TODO
        if flags & 14:
            if flags & 2:
                index = bullet_type.launch_anim2_index
                launch_mult = bullet_type.launch_anim_penalties[0]
            elif flags & 4:
                index = bullet_type.launch_anim4_index
                launch_mult = bullet_type.launch_anim_penalties[1]
            else:
                index = bullet_type.launch_anim8_index
                launch_mult = bullet_type.launch_anim_penalties[2]
            self.dx, self.dy = self.dx * launch_mult, self.dy * launch_mult
            self._sprite = Sprite()
            self._anmrunner = ANMRunner(bullet_type.anm_wrapper,
                                        index, self._sprite,
                                        bullet_type.launch_anim_offsets[sprite_idx_offset])
            self._anmrunner.run_frame()
        else:
            self.launch()

        if self.player_bullet:
            self._sprite.angle = angle - pi
        else:
            self._sprite.angle = angle


    cpdef is_visible(Bullet self, screen_width, screen_height):
        tx, ty, tw, th = self._sprite.texcoords
        x, y = self.x, self.y

        max_x = tw / 2.
        max_y = th / 2.

        if (max_x < x - screen_width
            or max_x < -x
            or max_y < y - screen_height
            or max_y < -y):
            return False
        return True


    def set_anim(Bullet self, sprite_idx_offset=None):
        if sprite_idx_offset is not None:
            self.sprite_idx_offset = sprite_idx_offset

        bt = self._bullet_type
        self._sprite = Sprite()
        if self.player_bullet:
            self._sprite.angle = self.angle - pi
        else:
            self._sprite.angle = self.angle
        self._anmrunner = ANMRunner(bt.anm_wrapper, bt.anim_index,
                                    self._sprite, self.sprite_idx_offset)
        self._anmrunner.run_frame()


    def launch(Bullet self):
        self._state = LAUNCHED
        self.frame = 0
        self.set_anim()
        self.dx, self.dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed
        if self.flags & 1:
            self.speed_interpolator = Interpolator((self.speed + 5.,), 0,
                                                   (self.speed,), 16)


    def collide(Bullet self):
        self.cancel()


    def cancel(Bullet self):
        # Cancel animation
        bt = self._bullet_type
        self._sprite = Sprite()
        if self.player_bullet:
            self._sprite.angle = self.angle - pi
        else:
            self._sprite.angle = self.angle
        self._anmrunner = ANMRunner(bt.anm_wrapper, bt.cancel_anim_index,
                                    self._sprite, bt.launch_anim_offsets[self.sprite_idx_offset])
        self._anmrunner.run_frame()
        self.dx, self.dy = self.dx / 2., self.dy / 2.

        # Change update method
        self._state = CANCELLED

        # Do not use this one for collisions anymore
        if self.player_bullet:
            self._game.players_bullets.remove(self)
        else:
            self._game.bullets.remove(self)
        self._game.cancelled_bullets.append(self)


    def update(Bullet self):
        if self._anmrunner is not None and not self._anmrunner.run_frame():
            if self._state == LAUNCHING:
                #TODO: check if it doesn't skip a frame
                self.launch()
            elif self._state == CANCELLED:
                self._removed = True
            else:
                self._anmrunner = None

        if self._state == LAUNCHING:
            pass
        elif self._state == CANCELLED:
            pass
        elif self.flags & 1:
            # Initial speed burst
            #TODO: use frame instead of interpolator?
            if not self.speed_interpolator:
                self.flags &= ~1
        elif self.flags & 16:
            # Each frame, add a vector to the speed vector
            length, angle = self.attributes[4:6]
            angle = self.angle if angle < -900.0 else angle #TODO: is that right?
            self.dx += cos(angle) * length
            self.dy += sin(angle) * length
            self.speed = (self.dx ** 2 + self.dy ** 2) ** 0.5
            self.angle = self._sprite.angle = atan2(self.dy, self.dx)
            if self._sprite.automatic_orientation:
                self._sprite._changed = True
            if self.frame == self.attributes[0]: #TODO: include last frame, or not?
                self.flags &= ~16
        elif self.flags & 32:
            # Each frame, accelerate and rotate
            #TODO: check
            acceleration, angular_speed = self.attributes[4:6]
            self.speed += acceleration
            self.angle += angular_speed
            self.dx = cos(self.angle) * self.speed
            self.dy = sin(self.angle) * self.speed
            self._sprite.angle = self.angle
            if self._sprite.automatic_orientation:
                self._sprite._changed = True
            if self.frame == self.attributes[0]:
                self.flags &= ~32
        elif self.flags & 448:
            #TODO: check
            frame, count = self.attributes[0:2]
            angle, speed = self.attributes[4:6]
            if self.frame % frame == 0:
                count = count - 1

                if self.frame != 0:
                    self.speed = speed

                    if self.flags & 64:
                        self.angle += angle
                    elif self.flags & 128:
                        self.angle = atan2(self.target.y - self.y,
                                           self.target.x - self.x) + angle
                    elif self.flags & 256:
                        self.angle = angle

                    self.dx = cos(self.angle) * self.speed
                    self.dy = sin(self.angle) * self.speed
                    self._sprite.angle = self.angle
                    if self._sprite.automatic_orientation:
                        self._sprite._changed = True

                if count >= 0:
                    self.speed_interpolator = Interpolator((self.speed,), self.frame,
                                                           (0.,), self.frame + frame - 1)
                else:
                    self.flags &= ~448

                self.attributes[1] = count
        #TODO: other flags

        # Common updates

        if self.speed_interpolator:
            self.speed_interpolator.update(self.frame)
            self.speed, = self.speed_interpolator.values
            self.dx = cos(self.angle) * self.speed
            self.dy = sin(self.angle) * self.speed

        self.x += self.dx
        self.y += self.dy

        self.frame += 1

        # Filter out-of-screen bullets and handle special flags
        #TODO: flags 1024 and 2048
        if self.flags & 448:
            self._was_visible = False
        elif self.is_visible(self._game.width, self._game.height):
            self._was_visible = True
        elif self._was_visible:
            # Filter out-of-screen bullets
            self._removed = True

