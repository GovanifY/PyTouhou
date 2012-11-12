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
    cdef public unsigned int state, flags, frame, sprite_idx_offset
    cdef public double dx, dy, angle, speed #TODO
    cdef public object player_bullet, target
    cdef public object _game, _bullet_type
    cdef public object sprite, anmrunner, removed, was_visible, objects
    cdef public object attributes, damage, hitbox, speed_interpolator, grazed
    cdef public object x, y #TODO

    def __init__(self, pos, bullet_type, sprite_idx_offset,
                       angle, speed, attributes, flags, target, game,
                       player_bullet=False, damage=0, hitbox=None):
        self._game = game
        self._bullet_type = bullet_type
        self.state = LAUNCHING
        self.sprite = None
        self.anmrunner = None
        self.removed = False
        self.was_visible = True
        self.objects = [self]

        if hitbox:
            self.hitbox = (hitbox[0], hitbox[1])
        else:
            self.hitbox = (bullet_type.hitbox_size, bullet_type.hitbox_size)

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
            self.sprite = Sprite()
            self.anmrunner = ANMRunner(bullet_type.anm_wrapper,
                                        index, self.sprite,
                                        bullet_type.launch_anim_offsets[sprite_idx_offset])
            self.anmrunner.run_frame()
        else:
            self.launch()

        if self.player_bullet:
            self.sprite.angle = angle - pi
        else:
            self.sprite.angle = angle


    cpdef is_visible(Bullet self, screen_width, screen_height):
        tx, ty, tw, th = self.sprite.texcoords
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
        self.sprite = Sprite()
        if self.player_bullet:
            self.sprite.angle = self.angle - pi
        else:
            self.sprite.angle = self.angle
        self.anmrunner = ANMRunner(bt.anm_wrapper, bt.anim_index,
                                   self.sprite, self.sprite_idx_offset)
        self.anmrunner.run_frame()


    def launch(Bullet self):
        self.state = LAUNCHED
        self.frame = 0
        self.set_anim()
        self.dx, self.dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed

        if self.flags & 1:
            self.speed_interpolator = Interpolator((self.speed + 5.,), 0,
                                                   (self.speed,), 16)


    def collide(Bullet self):
        self.cancel()
        self._game.new_particle((self.x, self.y), 10, 256) #TODO: find the real size.


    def cancel(Bullet self):
        # Cancel animation
        bt = self._bullet_type
        self.sprite = Sprite()
        if self.player_bullet:
            self.sprite.angle = self.angle - pi
        else:
            self.sprite.angle = self.angle
        self.anmrunner = ANMRunner(bt.anm_wrapper, bt.cancel_anim_index,
                                   self.sprite, bt.launch_anim_offsets[self.sprite_idx_offset])
        self.anmrunner.run_frame()
        self.dx, self.dy = self.dx / 2., self.dy / 2.

        self.state = CANCELLED


    def update(Bullet self):
        if self.anmrunner is not None and not self.anmrunner.run_frame():
            if self.state == LAUNCHING:
                #TODO: check if it doesn't skip a frame
                self.launch()
            elif self.state == CANCELLED:
                self.removed = True
            else:
                self.anmrunner = None

        if self.state == LAUNCHING:
            pass
        elif self.state == CANCELLED:
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
            self.angle = self.sprite.angle = atan2(self.dy, self.dx)
            if self.sprite.automatic_orientation:
                self.sprite.changed = True
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
            self.sprite.angle = self.angle
            if self.sprite.automatic_orientation:
                self.sprite.changed = True
            if self.frame == self.attributes[0]:
                self.flags &= ~32
        elif self.flags & 448:
            #TODO: check
            frame, count = self.attributes[0:2]
            angle, speed = self.attributes[4:6]
            if self.frame % frame == 0:
                count = count - 1

                if self.frame != 0:
                    self.speed = self.speed if speed < -900 else speed

                    if self.flags & 64:
                        self.angle += angle
                    elif self.flags & 128:
                        self.angle = atan2(self.target.y - self.y,
                                           self.target.x - self.x) + angle
                    elif self.flags & 256:
                        self.angle = angle

                    self.dx = cos(self.angle) * self.speed
                    self.dy = sin(self.angle) * self.speed
                    self.sprite.angle = self.angle
                    if self.sprite.automatic_orientation:
                        self.sprite.changed = True

                if count >= 0:
                    self.speed_interpolator = Interpolator((self.speed,), self.frame,
                                                           (0.,), self.frame + frame - 1)
                else:
                    self.flags &= ~448

                self.attributes[1] = count

        # Common updates

        if self.speed_interpolator:
            self.speed_interpolator.update(self.frame)
            speed, = self.speed_interpolator.values
            self.dx = cos(self.angle) * speed
            self.dy = sin(self.angle) * speed

        self.x += self.dx
        self.y += self.dy

        self.frame += 1

        # Filter out-of-screen bullets and handle special flags
        if self.flags & 448:
            self.was_visible = False
        elif self.is_visible(self._game.width, self._game.height):
            self.was_visible = True
        elif self.was_visible:
            self.removed = True
            if self.flags & (1024 | 2048) and self.attributes[0] > 0:
                # Bounce!
                if self.x < 0 or self.x > self._game.width:
                    self.angle = pi - self.angle
                    self.removed = False
                if self.y < 0 or ((self.flags & 1024) and self.y > self._game.height):
                    self.angle = -self.angle
                    self.removed = False
                self.sprite.angle = self.angle
                if self.sprite.automatic_orientation:
                    self.sprite.changed = True
                self.dx = cos(self.angle) * self.speed
                self.dy = sin(self.angle) * self.speed
                self.attributes[0] -= 1

