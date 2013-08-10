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

class Sprite(object):
    def __init__(self, width_override=0, height_override=0):
        self.anm = None
        self.removed = False
        self.changed = True
        self.visible = True

        self.width_override = width_override
        self.height_override = height_override
        self.angle = 0
        self.force_rotation = False

        self.scale_interpolator = None
        self.fade_interpolator = None
        self.offset_interpolator = None
        self.rotation_interpolator = None
        self.color_interpolator = None

        self.automatic_orientation = False

        self.blendfunc = 0 # 0 = Normal, 1 = saturate #TODO: proper constants

        self.texcoords = (0, 0, 0, 0) # x, y, width, height
        self.dest_offset = (0., 0., 0.)
        self.allow_dest_offset = False
        self.texoffsets = (0., 0.)
        self.mirrored = False
        self.rescale = (1., 1.)
        self.scale_speed = (0., 0.)
        self.rotations_3d = (0., 0., 0.)
        self.rotations_speed_3d = (0., 0., 0.)
        self.corner_relative_placement = False
        self.frame = 0
        self.color = (255, 255, 255)
        self.alpha = 255

        self._rendering_data = None


    def fade(self, duration, alpha, formula=None):
        self.fade_interpolator = Interpolator((self.alpha,), self.frame,
                                              (alpha,), self.frame + duration,
                                              formula)


    def scale_in(self, duration, sx, sy, formula=None):
        self.scale_interpolator = Interpolator(self.rescale, self.frame,
                                               (sx, sy), self.frame + duration,
                                               formula)


    def move_in(self, duration, x, y, z, formula=None):
        self.offset_interpolator = Interpolator(self.dest_offset, self.frame,
                                                (x, y, z), self.frame + duration,
                                                formula)


    def rotate_in(self, duration, rx, ry, rz, formula=None):
        self.rotation_interpolator = Interpolator(self.rotations_3d, self.frame,
                                                  (rx, ry, rz), self.frame + duration,
                                                  formula)


    def change_color_in(self, duration, r, g, b, formula=None):
        self.color_interpolator = Interpolator(self.color, self.frame,
                                               (r, g, b), self.frame + duration,
                                               formula)


    def update_orientation(self, angle_base=0., force_rotation=False):
        if (self.angle != angle_base or self.force_rotation != force_rotation):
            self.angle = angle_base
            self.force_rotation = force_rotation
            self.changed = True


    def copy(self):
        sprite = Sprite(self.width_override, self.height_override)

        sprite.blendfunc = self.blendfunc
        sprite.frame = self.frame
        sprite.angle = self.angle

        sprite.removed = self.removed
        sprite.changed = self.changed
        sprite.visible = self.visible
        sprite.force_rotation = self.force_rotation
        sprite.automatic_orientation = self.automatic_orientation
        sprite.allow_dest_offset = self.allow_dest_offset
        sprite.mirrored = self.mirrored
        sprite.corner_relative_placement = self.corner_relative_placement

        sprite.scale_interpolator = self.scale_interpolator
        sprite.fade_interpolator = self.fade_interpolator
        sprite.offset_interpolator = self.offset_interpolator
        sprite.rotation_interpolator = self.rotation_interpolator
        sprite.color_interpolator = self.color_interpolator

        sprite.texcoords = self.texcoords
        sprite.dest_offset = self.dest_offset
        sprite.texoffsets = self.texoffsets
        sprite.rescale = self.rescale
        sprite.scale_speed = self.scale_speed
        sprite.rotations_3d = self.rotations_3d
        sprite.rotations_speed_3d = self.rotations_speed_3d
        sprite.color = self.color

        sprite.alpha = self.alpha
        sprite.anm = self.anm
        sprite._rendering_data = self._rendering_data

        return sprite


    def update(self):
        self.frame += 1

        if self.rotations_speed_3d != (0., 0., 0.):
            ax, ay, az = self.rotations_3d
            sax, say, saz = self.rotations_speed_3d
            self.rotations_3d = ax + sax, ay + say, az + saz
            self.changed = True
        elif self.rotation_interpolator:
            self.rotation_interpolator.update(self.frame)
            self.rotations_3d = self.rotation_interpolator.values
            self.changed = True

        if self.scale_speed != (0., 0.):
            rx, ry = self.rescale
            rsx, rsy = self.scale_speed
            self.rescale = rx + rsx, ry + rsy
            self.changed = True

        if self.fade_interpolator:
            self.fade_interpolator.update(self.frame)
            self.alpha = self.fade_interpolator.values[0]
            self.changed = True

        if self.scale_interpolator:
            self.scale_interpolator.update(self.frame)
            self.rescale = self.scale_interpolator.values
            self.changed = True

        if self.offset_interpolator:
            self.offset_interpolator.update(self.frame)
            self.dest_offset = self.offset_interpolator.values
            self.changed = True

        if self.color_interpolator:
            self.color_interpolator.update(self.frame)
            self.color = self.color_interpolator.values
            self.changed = True
