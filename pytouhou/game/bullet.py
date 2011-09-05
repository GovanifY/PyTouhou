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
        #    if flags & 2: #TODO: Huh?!
        #        index = 14
        #    elif flags & 4:
        #        index = 15
        #    else:
        #        index = 19
        #    self._sprite = Sprite()
        #    self._anmrunner = ANMRunner(self._game_state.resource_loader.get_anm_wrapper(('etama3.anm',)), #TODO
        #                                index, self._sprite, 0) #TODO: offset
        #    self._anmrunner.run_frame()

        self.flags = flags
        self.attributes = list(attributes)

        self.x, self.y = pos
        self.angle = angle
        self.speed = speed

        if flags & 1:
            self.speed_interpolator = Interpolator((speed + 5.,))
            self.speed_interpolator.set_interpolation_start(0, (speed + 5.,))
            self.speed_interpolator.set_interpolation_end(16, (speed,))
        if flags & 448:
            self.speed_interpolator = Interpolator((speed,))
            self.speed_interpolator.set_interpolation_start(0, (speed,))
            self.speed_interpolator.set_interpolation_end(attributes[0] - 1, (0,)) # TODO: really -1? Without, the new speed isn’t set.


    def get_player_angle(self):
        return atan2(self.player.y - self.y, self.player.x - self.x)


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
        sprite.update_vertices_uvs_colors()
        key = sprite.anm.first_name, sprite.anm.secondary_name
        key = (key, sprite.blendfunc)
        rec = objects_by_texture.setdefault(key, ([], [], []))
        vertices = ((x + self.x, y + self.y, z) for x, y, z in sprite._vertices)
        rec[0].extend(vertices)
        rec[1].extend(sprite._uvs)
        rec[2].extend(sprite._colors)


    def update(self):
        if not self._sprite or self._sprite._removed:
            self._launched = True
            self._sprite = Sprite()
            anm_wrapper = self._game_state.resource_loader.get_anm_wrapper(('etama3.anm',)) #TODO
            self._anmrunner = ANMRunner(anm_wrapper, self.anim_idx,
                                        self._sprite, self.sprite_idx_offset)

        self._anmrunner.run_frame()
        self._sprite.update(angle_base=self.angle)

        #TODO: flags
        x, y = self.x, self.y

        if self.flags & 16:
            frame, count = self.attributes[0:2]
            length, angle = self.attributes[4:6]
            angle = self.angle if angle < -900.0 else angle #TODO: is that right?
            dx = cos(self.angle) * self.speed + cos(angle) * length
            dy = sin(self.angle) * self.speed + sin(angle) * length
            self.speed = (dx ** 2 + dy ** 2) ** 0.5
            self.angle = atan2(dy, dx)
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
            if self.frame == frame:
                if count > 0:
                    self.attributes[1] -= 1
                else:
                    self.flags ^= 32
        elif self.flags & 448:
            #TODO: check
            frame, count = self.attributes[0:2]
            angle, speed = self.attributes[4:6]
            if frame == self.frame:
                count = count - 1

                if self.flags & 64:
                    self.angle = self.angle + angle
                elif self.flags & 128:
                    self.angle = self.get_player_angle() + angle
                elif self.flags & 256:
                    self.angle = angle

                if count:
                    self.speed_interpolator.set_interpolation_start(self.frame, (speed,))
                    self.speed_interpolator.set_interpolation_end(self.frame + frame - 1, (0,)) # TODO: really -1? Without, the new speed isn’t set.
                else:
                    self.flags &= ~448
                    self.speed = speed

                self.attributes[1] = count
        #TODO: other flags

        if self.speed_interpolator:
            self.speed_interpolator.update(self.frame)
            self.speed, = self.speed_interpolator.values

        dx, dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed
        self.x, self.y = x + dx, y + dy

        self.frame += 1

