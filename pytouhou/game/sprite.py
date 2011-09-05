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


from pytouhou.utils.interpolator import Interpolator


class Sprite(object):
    def __init__(self):
        self.anm = None
        self._removed = False
        self._changed = False

        self.width_override = 0
        self.height_override = 0
        self.angle = 0
        self.force_rotation = False

        self.scale_interpolator = None
        self.fade_interpolator = None
        self.offset_interpolator = None

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


    def fade(self, duration, alpha, formula):
        if not self.fade_interpolator:
            self.fade_interpolator = Interpolator((self.alpha,), formula)
            self.fade_interpolator.set_interpolation_start(self.frame, (self.alpha,))
            self.fade_interpolator.set_interpolation_end(self.frame + duration - 1, (alpha,))


    def scale_in(self, duration, sx, sy, formula):
        if not self.scale_interpolator:
            self.scale_interpolator = Interpolator(self.rescale, formula)
            self.scale_interpolator.set_interpolation_start(self.frame, self.rescale)
            self.scale_interpolator.set_interpolation_end(self.frame + duration - 1, (sx, sy))


    def move_in(self, duration, x, y, z, formula):
        if not self.offset_interpolator:
            self.offset_interpolator = Interpolator(self.dest_offset, formula)
            self.offset_interpolator.set_interpolation_start(self.frame, self.dest_offset)
            self.offset_interpolator.set_interpolation_end(self.frame + duration - 1, (x, y, z))


    def update(self, override_width=0, override_height=0, angle_base=0., force_rotation=False):
        if (override_width != self.width_override
            or override_height != self.height_override
            or self.angle != angle_base
            or self.force_rotation != force_rotation
            or self.scale_interpolator
            or self.fade_interpolator
            or self.offset_interpolator):

            self._changed = True
            self.width_override = override_width
            self.height_override = override_height
            self.angle = angle_base
            self.force_rotation = force_rotation

        if self.rotations_speed_3d != (0., 0., 0.):
            ax, ay, az = self.rotations_3d
            sax, say, saz = self.rotations_speed_3d
            self.rotations_3d = ax + sax, ay + say, az + saz
            self._changed = True

        if self.scale_speed != (0., 0.):
            rx, ry = self.rescale
            rsx, rsy = self.scale_speed
            self.rescale = rx + rsx, ry + rsy
            self._changed = True

        self.frame += 1

