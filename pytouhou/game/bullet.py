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
    __slots__ = ('x', 'y', 'angle', 'speed', 'frame', 'grazed',
                 'flags', 'attributes', 'anim_idx', 'sprite_idx_offset', 'player',
                 'speed_interpolator',
                 '_game_state', '_sprite', '_anmrunner',
                 '_removed', '_launched')

    def __init__(self, pos, anim_idx, sprite_idx_offset,
                       angle, speed, attributes, flags, player, game_state):
        self._game_state = game_state
        self._sprite = None
        self._anmrunner = None
        self._removed = False
        self._launched = False

        self.speed_interpolator = None
        self.frame = 0
        self.grazed = False

        self.player = player

        self.anim_idx = anim_idx
        self.sprite_idx_offset = sprite_idx_offset

        #TODO
        #if flags & (2|4|8):
        #    index = {2: 11, 4: 12, 8: 13}[flags & (2|4|8)]
        #    self._sprite = Sprite()
        #    self._anmrunner = ANMRunner(self._game_state.resources.etama_anm_wrappers[0],
        #                                index, self._sprite, sprite_idx_offset)

        self.flags = flags
        self.attributes = list(attributes)

        self.x, self.y = pos
        self.angle = angle
        self.speed = speed

        if flags & 1:
            self.speed_interpolator = Interpolator((speed + 5.,))
            self.speed_interpolator.set_interpolation_start(0, (speed + 5.,))
            self.speed_interpolator.set_interpolation_end(16, (speed,))


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
        sprite = self._sprite
        key = sprite.anm.first_name, sprite.anm.secondary_name
        key = (key, sprite.blendfunc)
        if not key in objects_by_texture:
            objects_by_texture[key] = (0, [], [], [])
        vertices = ((x + self.x, y + self.y, z) for x, y, z in sprite._vertices)
        objects_by_texture[key][1].extend(vertices)
        objects_by_texture[key][2].extend(sprite._uvs)
        objects_by_texture[key][3].extend(sprite._colors)


    def update(self):
        if not self._sprite or self._sprite._removed:
            self._launched = True
            self._sprite = Sprite()
            self._anmrunner = ANMRunner(self._game_state.resources.etama_anm_wrappers[0], #TODO
                                        self.anim_idx, self._sprite, self.sprite_idx_offset)

        if self._anmrunner and not self._anmrunner.run_frame():
            self._anmrunner = None

        self._sprite.update()
        if self._sprite._changed: #TODO
            angle = pi/2.-self.angle if self._sprite.automatic_orientation else 0.
            self._sprite.update_vertices_uvs_colors(angle_base=angle)

        #TODO: flags
        x, y = self.x, self.y

        if self.flags & 16:
            #TODO: duration, count
            length, angle = self.attributes[4:6]
            angle = self.angle if angle < -900.0 else angle #TODO: is that right?
            dx = cos(self.angle) * self.speed + cos(angle) * length
            dy = sin(self.angle) * self.speed + sin(angle) * length
            self.speed = (dx ** 2 + dy ** 2) ** 0.5
            self.angle = atan2(dy, dx)
        elif self.flags & 32:
            #TODO: duration, count
            #TODO: check
            acceleration, angular_speed = self.attributes[4:6]
            self.speed += acceleration
            self.angle += angular_speed
        #TODO: other flags

        if self.speed_interpolator:
            self.speed_interpolator.update(self.frame)
            self.speed, = self.speed_interpolator.values

        dx, dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed
        self.x, self.y = x + dx, y + dy

        self.frame += 1

