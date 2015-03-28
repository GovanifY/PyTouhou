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

from libc.math cimport cos, sin, M_PI as pi

from pytouhou.game.game cimport Game
from pytouhou.vm import ANMRunner


cdef class LaserLaunchAnim(Element):
    def __init__(self, Laser laser, anm, unsigned long index):
        Element.__init__(self, (0, 0))

        self._laser = laser
        self.sprite = Sprite()
        self.sprite.anm = anm
        self.sprite.texcoords = anm.sprites[index]
        self.sprite.blendfunc = 1


    cpdef update(self):
        laser = self._laser
        length = <double>min(laser.end_offset - laser.start_offset, laser.max_length)
        offset = laser.end_offset - length
        dx, dy = cos(laser.angle), sin(laser.angle)

        self.x = laser.base_pos[0] + offset * dx
        self.y = laser.base_pos[1] + offset * dy

        scale = laser.width / 10. - (offset - laser.start_offset) #TODO: check
        self.sprite._rescale[:] = [scale, scale]
        self.sprite.changed = True

        if laser.removed or scale <= 0.:
            self.removed = True



cdef class Laser(Element):
    def __init__(self, tuple base_pos, LaserType laser_type,
                 unsigned long sprite_idx_offset, double angle, double speed,
                 double start_offset, double end_offset, double max_length,
                 double width, unsigned long start_duration,
                 unsigned long duration, unsigned long stop_duration,
                 unsigned long grazing_delay,
                 unsigned long grazing_extra_duration, Game game):
        Element.__init__(self, (0, 0))

        launch_anim = LaserLaunchAnim(self, laser_type.anm,
                                      laser_type.launch_anim_offsets[sprite_idx_offset]
                                      + laser_type.launch_sprite_idx)
        game.effects.append(launch_anim)
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
        self.set_base_pos(base_pos[0], base_pos[1])
        self.angle = angle
        self.speed = speed
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.max_length = max_length
        self.width = width

        self.set_anim()


    cdef bint set_anim(self, long sprite_idx_offset=-1) except True:
        if sprite_idx_offset >= 0:
            self.sprite_idx_offset = sprite_idx_offset

        lt = self._laser_type
        self.sprite = Sprite()
        self.sprite.angle = self.angle
        self.anmrunner = ANMRunner(lt.anm, lt.anim_index,
                                   self.sprite, self.sprite_idx_offset)


    cpdef set_base_pos(self, double x, double y):
        self.base_pos[:] = [x, y]


    cdef bint _check_collision(self, double point[2], double border_size):
        cdef double c1[2]
        cdef double c2[2]
        cdef double c3[2]

        x, y = point[0] - self.base_pos[0], point[1] - self.base_pos[1]
        dx, dy = cos(self.angle), sin(self.angle)
        dx2, dy2 = -dy, dx

        length = <double>min(self.end_offset - self.start_offset, self.max_length)
        offset = self.end_offset - length - border_size / 2.
        end_offset = self.end_offset + border_size / 2.
        half_width = self.width / 4. + border_size / 2.

        c1[:] = [dx * offset - dx2 * half_width, dy * offset - dy2 * half_width]
        c2[:] = [dx * offset + dx2 * half_width, dy * offset + dy2 * half_width]
        c3[:] = [dx * end_offset + dx2 * half_width, dy * end_offset + dy2 * half_width]
        vx, vy = x - c2[0], y - c2[1]
        v1x, v1y = c1[0] - c2[0], c1[1] - c2[1]
        v2x, v2y = c3[0] - c2[0], c3[1] - c2[1]

        return (0 <= vx * v1x + vy * v1y <= v1x * v1x + v1y * v1y
                and 0 <= vx * v2x + vy * v2y <= v2x * v2x + v2y * v2y)


    cdef bint check_collision(self, double point[2]):
        if self.state != STARTED:
            return False

        return self._check_collision(point, 2.5)


    cdef bint check_grazing(self, double point[2]):
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
        length = <double>min(self.end_offset - self.start_offset, self.max_length)
        offset = self.end_offset - length
        dx, dy = cos(self.angle), sin(self.angle)
        while self.start_offset <= offset < self.end_offset:
            yield (self.base_pos[0] + offset * dx, self.base_pos[1] + offset * dy)
            offset += 48.


    cpdef cancel(self):
        self.grazing_extra_duration = 0
        if self.state != STOPPING:
            self.frame = 0
            self.state = STOPPING


    cpdef update(self):
        if self.anmrunner is not None and not self.anmrunner.run_frame():
            self.anmrunner = None

        self.end_offset += self.speed

        length = <double>min(self.end_offset - self.start_offset, self.max_length) # TODO
        width = 0.
        if self.state == STARTING:
            if self.frame == self.start_duration:
                self.frame = 0
                self.state = STARTED
            else:
                width = self.width * float(self.frame) / self.start_duration #TODO
        elif self.state == STARTED:
            width = self.width #TODO
            if self.frame == self.duration:
                self.frame = 0
                self.state = STOPPING
        elif self.state == STOPPING:
            if self.frame == self.stop_duration:
                self.removed = True
            else:
                width = self.width * (1. - float(self.frame) / self.stop_duration) #TODO

        offset = self.end_offset - length / 2.
        self.x = self.base_pos[0] + offset * cos(self.angle)
        self.y = self.base_pos[1] + offset * sin(self.angle)
        self.sprite.visible = (width > 0 and length > 0)
        self.sprite.width_override = width
        self.sprite.height_override = length

        self.sprite.update_orientation(pi/2. - self.angle, True)
        self.sprite.changed = True #TODO

        self.frame += 1


cdef class PlayerLaser(Element):
    def __init__(self, LaserType laser_type, unsigned long sprite_idx_offset,
                 tuple hitbox, unsigned long damage, double angle,
                 double offset, unsigned long duration, Element origin):
        Element.__init__(self)

        self._laser_type = laser_type
        self.origin = origin

        self.hitbox[:] = [hitbox[0], hitbox[1]]

        self.frame = 0
        self.duration = duration

        self.sprite_idx_offset = sprite_idx_offset
        self.angle = angle
        self.offset = offset
        self.damage = damage

        self.set_anim()


    cdef bint set_anim(self, long sprite_idx_offset=-1) except True:
        if sprite_idx_offset >= 0:
            self.sprite_idx_offset = sprite_idx_offset

        lt = self._laser_type
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(lt.anm, lt.anim_index,
                                   self.sprite, self.sprite_idx_offset)
        #self.sprite.blendfunc = 1 #XXX


    cdef bint cancel(self) except True:
        self.anmrunner.interrupt(1)


    cdef bint update(self) except True:
        if self.anmrunner is not None and not self.anmrunner.run_frame():
            self.anmrunner = None
            self.removed = True

        length = self.origin.y
        if self.frame == self.duration:
            self.cancel()

        self.sprite.visible = (length > 0)
        self.sprite.height_override = length
        self.sprite.changed = True #TODO

        self.x = self.origin.x + self.offset * cos(self.angle)
        self.y = self.origin.y / 2. + self.offset * sin(self.angle)

        self.frame += 1
