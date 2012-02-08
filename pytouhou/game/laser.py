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


class Laser(object):
    def __init__(self, base_pos, laser_type, sprite_idx_offset,
                       angle, speed, start_offset, end_offset, max_length, width,
                       start_duration, duration, stop_duration,
                       grazing_delay, grazing_extra_duration,
                       game):
        self._game = game
        #TODO: aux sprite
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


    def get_bullets_pos(self):
        #TODO: check
        length = min(self.end_offset - self.start_offset, self.max_length)
        offset = self.end_offset - length
        dx, dy = cos(self.angle), sin(self.angle)
        while self.start_offset <= offset < self.end_offset:
            yield (self.x + offset * dx, self.y + offset * dy)
            offset += 48.


    def cancel(self):
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

