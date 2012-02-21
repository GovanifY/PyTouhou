# -*- encoding: utf-8 -*-
##
## Copyright (C) 2012 Thibaut Girka <thib@sitedethib.com>
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

from math import cos, sin, pi

from pytouhou.vm.anmrunner import ANMRunner
from pytouhou.game.sprite import Sprite


STARTING, STARTED, STOPPING = range(3)


class LaserLaunchAnim(object):
    def __init__(self, laser, anm_wrapper, index):
        self._laser = laser
        self._sprite = Sprite()
        self._sprite.anm, self._sprite.texcoords = anm_wrapper.get_sprite(index)
        self._sprite.blendfunc = 1
        self._removed = False
        self.x, self.y = 0, 0


    def update(self):
        laser = self._laser
        length = min(laser.end_offset - laser.start_offset, laser.max_length)
        offset = laser.end_offset - length
        dx, dy = cos(laser.angle), sin(laser.angle)

        self.x = laser.base_pos[0] + offset * dx
        self.y = laser.base_pos[1] + offset * dy

        scale = laser.width / 10. - (offset - laser.start_offset)
        self._sprite.rescale = (scale, scale)
        self._sprite._changed = True

        if laser._removed or scale <= 0.:
            self._removed = True



class Laser(object):
    def __init__(self, base_pos, laser_type, sprite_idx_offset,
                       angle, speed, start_offset, end_offset, max_length, width,
                       start_duration, duration, stop_duration,
                       grazing_delay, grazing_extra_duration,
                       game):
        self._game = game
        launch_anim = LaserLaunchAnim(self, laser_type.anm_wrapper,
                                      laser_type.launch_anim_offsets[sprite_idx_offset]
                                      + laser_type.launch_sprite_idx)
        self._game.effects.append(launch_anim)
        self._sprite = None
        self._anmrunner = None
        self._removed = False
        self._laser_type = laser_type
        self.state = STARTING

        #TODO: hitbox

        self.frame = 0
        self.start_duration = start_duration
        self.duration = duration
        self.stop_duration = stop_duration
        self.grazing_delay = grazing_delay
        self.grazing_extra_duration = grazing_extra_duration

        self.sprite_idx_offset = sprite_idx_offset
        self.base_pos = base_pos
        self.x, self.y = 0, 0
        self.angle = angle
        self.speed = speed
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.max_length = max_length
        self.width = width

        self.set_anim()


    def set_anim(self, sprite_idx_offset=None):
        if sprite_idx_offset is not None:
            self.sprite_idx_offset = sprite_idx_offset

        lt = self._laser_type
        self._sprite = Sprite()
        self._sprite.angle = self.angle
        self._anmrunner = ANMRunner(lt.anm_wrapper, lt.anim_index,
                                    self._sprite, self.sprite_idx_offset)
        self._anmrunner.run_frame()


    def _check_collision(self, point, border_size):
        x, y = point[0] - self.base_pos[0], point[1] - self.base_pos[1]
        dx, dy = cos(self.angle), sin(self.angle)
        dx2, dy2 = -dy, dx

        length = min(self.end_offset - self.start_offset, self.max_length)
        offset = self.end_offset - length - border_size / 2.
        end_offset = self.end_offset + border_size / 2.
        half_width = self.width / 4. + border_size / 2.

        c1 = dx * offset - dx2 * half_width, dy * offset - dy2 * half_width
        c2 = dx * offset + dx2 * half_width, dy * offset + dy2 * half_width
        c3 = dx * end_offset + dx2 * half_width, dy * end_offset + dy2 * half_width
        vx, vy = x - c2[0], y - c2[1]
        v1x, v1y = c1[0] - c2[0], c1[1] - c2[1]
        v2x, v2y = c3[0] - c2[0], c3[1] - c2[1]

        return (0 <= vx * v1x + vy * v1y <= v1x * v1x + v1y * v1y
                and 0 <= vx * v2x + vy * v2y <= v2x * v2x + v2y * v2y)


    def check_collision(self, point):
        if self.state != STARTED:
            return False

        return self._check_collision(point, 2.5)


    def check_grazing(self, point):
        #TODO: quadruple check!
        if self.state == STOPPING and self.frame >= self.grazing_extra_duration:
            return False
        if self.state == STARTING and self.frame <= self.grazing_delay:
            return False
        if self.frame % 12 != 0:
            return False

        return self._check_collision(point, 96 + 2.5)


    def get_bullets_pos(self):
        #TODO: check
        length = min(self.end_offset - self.start_offset, self.max_length)
        offset = self.end_offset - length
        dx, dy = cos(self.angle), sin(self.angle)
        while self.start_offset <= offset < self.end_offset:
            yield (self.base_pos[0] + offset * dx, self.base_pos[1] + offset * dy)
            offset += 48.


    def cancel(self):
        self.grazing_extra_duration = 0
        if self.state != STOPPING:
            self.frame = 0
            self.state = STOPPING


    def update(self):
        if self._anmrunner is not None and not self._anmrunner.run_frame():
            self._anmrunner = None

        self.end_offset += self.speed

        length = min(self.end_offset - self.start_offset, self.max_length) # TODO
        if self.state == STARTING:
            if self.frame == self.start_duration:
                self.frame = 0
                self.state = STARTED
            else:
                width = self.width * float(self.frame) / self.start_duration #TODO
        if self.state == STARTED:
            width = self.width #TODO
            if self.frame == self.duration:
                self.frame = 0
                self.state = STOPPING
        if self.state == STOPPING:
            if self.frame == self.stop_duration:
                width = 0.
                self._removed = True
            else:
                width = self.width * (1. - float(self.frame) / self.stop_duration) #TODO

        offset = self.end_offset - length / 2.
        self.x, self.y = self.base_pos[0] + offset * cos(self.angle), self.base_pos[1] + offset * sin(self.angle)
        self._sprite.width_override = width or 0.01 #TODO
        self._sprite.height_override = length or 0.01 #TODO

        self._sprite.update_orientation(pi/2. - self.angle, True)
        self._sprite._changed = True #TODO

        self.frame += 1


class PlayerLaser(object):
    def __init__(self, laser_type, sprite_idx_offset, hitbox, damage,
                 angle, offset, duration, origin):
        self._sprite = None
        self._anmrunner = None
        self._removed = False
        self._laser_type = laser_type
        self.origin = origin

        self.hitbox_half_size = hitbox[0] / 2., hitbox[1] / 2.

        self.frame = 0
        self.duration = duration

        self.sprite_idx_offset = sprite_idx_offset
        self.angle = angle
        self.offset = offset
        self.damage = damage

        self.set_anim()


    @property
    def x(self):
        return self.origin.x + self.offset * cos(self.angle)


    @property
    def y(self):
        return self.origin.y / 2. + self.offset * sin(self.angle)


    def set_anim(self, sprite_idx_offset=None):
        if sprite_idx_offset is not None:
            self.sprite_idx_offset = sprite_idx_offset

        lt = self._laser_type
        self._sprite = Sprite()
        self._anmrunner = ANMRunner(lt.anm_wrapper, lt.anim_index,
                                    self._sprite, self.sprite_idx_offset)
        #self._sprite.blendfunc = 1 #XXX
        self._anmrunner.run_frame()


    def cancel(self):
        self._anmrunner.interrupt(1)


    def update(self):
        if self._anmrunner is not None and not self._anmrunner.run_frame():
            self._anmrunner = None
            self._removed = True

        length = self.origin.y
        if self.frame == self.duration:
            self.cancel()

        self._sprite.height_override = length or 0.01 #TODO
        self._sprite._changed = True #TODO

        self.frame += 1

