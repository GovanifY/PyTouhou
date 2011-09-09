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
    __slots__ = ('anm', '_removed', '_changed', 'width_override', 'height_override',
                 'angle', 'force_rotation', 'scale_interpolator', 'fade_interpolator',
                 'offset_interpolator', 'automatic_orientation', 'blendfunc',
                 'texcoords', 'dest_offset', 'allow_dest_offset', 'texoffsets',
                 'mirrored', 'rescale', 'scale_speed', 'rotations_3d',
                 'rotations_speed_3d', 'corner_relative_placement', 'frame',
                 'color', 'alpha', '_rendering_data')
    def __init__(self, width_override=0, height_override=0):
        self.anm = None
        self._removed = False
        self._changed = False

        self.width_override = width_override
        self.height_override = height_override
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
            self.fade_interpolator = Interpolator((self.alpha,), self.frame,
                                                  (alpha,), self.frame + duration,
                                                  formula)


    def scale_in(self, duration, sx, sy, formula):
        if not self.scale_interpolator:
            self.scale_interpolator = Interpolator(self.rescale, self.frame,
                                                   (sx, sy), self.frame + duration,
                                                   formula)


    def move_in(self, duration, x, y, z, formula):
        if not self.offset_interpolator:
            self.offset_interpolator = Interpolator(self.dest_offset, self.frame,
                                                    (x, y, z), self.frame + duration,
                                                    formula)


    def update_orientation(self, angle_base=0., force_rotation=False):
        if (self.angle != angle_base or self.force_rotation != force_rotation):
            self.angle = angle_base
            self.force_rotation = force_rotation
            self._changed = True

