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

cimport cython

from libc.math cimport cos, sin, atan2, M_PI as pi

from pytouhou.vm import ANMRunner
from pytouhou.game.sprite cimport Sprite


cdef class Bullet(Element):
    def __init__(self, pos, BulletType bullet_type, unsigned long sprite_idx_offset,
                       double angle, double speed, attributes, unsigned long flags, target, Game game,
                       long player=-1, unsigned long damage=0, tuple hitbox=None):
        cdef double launch_mult

        Element.__init__(self, pos)

        self._game = game
        self._bullet_type = bullet_type
        self.state = LAUNCHING
        self.was_visible = True

        if hitbox is not None:
            self.hitbox[:] = [hitbox[0], hitbox[1]]
        else:
            self.hitbox[:] = [bullet_type.hitbox_size, bullet_type.hitbox_size]

        self.speed_interpolator = None
        self.frame = 0
        self.grazed = False

        self.target = target

        self.sprite_idx_offset = sprite_idx_offset

        self.flags = flags
        self.attributes = list(attributes)

        self.angle = angle
        self.speed = speed
        self.dx, self.dy = cos(angle) * speed, sin(angle) * speed

        self.player = player
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
            self.anmrunner = ANMRunner(bullet_type.anm,
                                        index, self.sprite,
                                        bullet_type.launch_anim_offsets[sprite_idx_offset])
        else:
            self.launch()

        if self.player >= 0:
            self.sprite.angle = angle - pi
        else:
            self.sprite.angle = angle


    cdef bint is_visible(self, unsigned int screen_width, unsigned int screen_height) nogil:
        tw, th = self.sprite._texcoords[2], self.sprite._texcoords[3]
        x, y = self.x, self.y

        max_x = tw / 2
        max_y = th / 2

        if (max_x < x - screen_width
            or max_x < -x
            or max_y < y - screen_height
            or max_y < -y):
            return False
        return True


    cpdef set_anim(self, sprite_idx_offset=None):
        if sprite_idx_offset is not None:
            self.sprite_idx_offset = sprite_idx_offset

        bt = self._bullet_type
        self.sprite = Sprite()
        if self.player >= 0:
            self.sprite.angle = self.angle - pi
        else:
            self.sprite.angle = self.angle
        self.anmrunner = ANMRunner(bt.anm, bt.anim_index,
                                   self.sprite, self.sprite_idx_offset)


    cdef bint launch(self) except True:
        self.state = LAUNCHED
        self.frame = 0
        self.set_anim()
        self.dx, self.dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed

        if self.flags & 1:
            self.speed_interpolator = Interpolator((self.speed + 5.,), 0,
                                                   (self.speed,), 16)


    cdef bint collide(self) except True:
        self.cancel()
        self._game.new_particle((self.x, self.y), 10, 256) #TODO: find the real size.


    @cython.cdivision(True)
    cdef bint cancel(self) except True:
        # Cancel animation
        bt = self._bullet_type
        self.sprite = Sprite()
        if self.player >= 0:
            self.sprite.angle = self.angle - pi
            divisor = 8.
        else:
            self.sprite.angle = self.angle
            divisor = 2.
        self.anmrunner = ANMRunner(bt.anm, bt.cancel_anim_index,
                                   self.sprite, bt.launch_anim_offsets[self.sprite_idx_offset])
        self.dx /= divisor
        self.dy /= divisor

        self.state = CANCELLED


    cdef bint update(self) except True:
        cdef int frame, count, game_width, game_height
        cdef double length, angle, speed, acceleration, angular_speed

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
                count -= 1

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

        game_width, game_height = self._game.width, self._game.height

        # Filter out-of-screen bullets and handle special flags
        if self.flags & 448:
            self.was_visible = False
        elif self.is_visible(game_width, game_height):
            self.was_visible = True
        elif self.was_visible:
            self.removed = True
            if self.flags & (1024 | 2048) and self.attributes[0] > 0:
                # Bounce!
                if self.x < 0 or self.x > game_width:
                    self.angle = pi - self.angle
                    self.removed = False
                if self.y < 0 or ((self.flags & 1024) and self.y > game_height):
                    self.angle = -self.angle
                    self.removed = False
                self.sprite.angle = self.angle
                if self.sprite.automatic_orientation:
                    self.sprite.changed = True
                self.dx = cos(self.angle) * self.speed
                self.dy = sin(self.angle) * self.speed
                self.attributes[0] -= 1
