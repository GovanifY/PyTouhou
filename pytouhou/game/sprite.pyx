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

from libc.stdlib cimport free
from libc.string cimport memcpy


cdef class Sprite:
    def __dealloc__(self):
        if self._rendering_data != NULL:
            free(self._rendering_data)


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

        self._texcoords[:] = [0, 0, 0, 0] # x, y, width, height
        self._dest_offset[:] = [0., 0., 0.]
        self.allow_dest_offset = False
        self._texoffsets[:] = [0., 0.]
        self.mirrored = False
        self._rescale[:] = [1., 1.]
        self._scale_speed[:] = [0., 0.]
        self._rotations_3d[:] = [0., 0., 0.]
        self._rotations_speed_3d[:] = [0., 0., 0.]
        self.corner_relative_placement = False
        self.frame = 0

        # Cython treats unsigned char* variables as bytes, so we can’t use
        # slicing here.
        for i in range(4):
            self._color[i] = 255


    property scale_speed:
        def __get__(self):
            return (self._scale_speed[0], self._scale_speed[1])
        def __set__(self, value):
            self._scale_speed[:] = [value[0], value[1]]

    property texoffsets:
        def __get__(self):
            return (self._texoffsets[0], self._texoffsets[1])
        def __set__(self, value):
            self._texoffsets[:] = [value[0], value[1]]

    property rescale:
        def __get__(self):
            return (self._rescale[0], self._rescale[1])
        def __set__(self, value):
            self._rescale[:] = [value[0], value[1]]

    property dest_offset:
        def __get__(self):
            return (self._dest_offset[0], self._dest_offset[1], self._dest_offset[2])
        def __set__(self, value):
            self._dest_offset[:] = [value[0], value[1], value[2]]

    property rotations_speed_3d:
        def __get__(self):
            return (self._rotations_speed_3d[0], self._rotations_speed_3d[1], self._rotations_speed_3d[2])
        def __set__(self, value):
            self._rotations_speed_3d[:] = [value[0], value[1], value[2]]

    property rotations_3d:
        def __get__(self):
            return (self._rotations_3d[0], self._rotations_3d[1], self._rotations_3d[2])
        def __set__(self, value):
            self._rotations_3d[:] = [value[0], value[1], value[2]]

    property color:
        def __get__(self):
            return (self._color[0], self._color[1], self._color[2])
        def __set__(self, value):
            self._color[0] = value[0]
            self._color[1] = value[1]
            self._color[2] = value[2]

    property alpha:
        def __get__(self):
            return self._color[3]
        def __set__(self, value):
            self._color[3] = value

    property texcoords:
        def __get__(self):
            return (self._texcoords[0], self._texcoords[1], self._texcoords[2], self._texcoords[3])
        def __set__(self, value):
            self._texcoords[:] = [value[0], value[1], value[2], value[3]]


    cpdef fade(self, unsigned int duration, alpha, formula=None):
        self.fade_interpolator = Interpolator((self._color[3],), self.frame,
                                              (alpha,), self.frame + duration,
                                              formula)


    cpdef scale_in(self, unsigned int duration, sx, sy, formula=None):
        self.scale_interpolator = Interpolator(self.rescale, self.frame,
                                               (sx, sy), self.frame + duration,
                                               formula)


    cpdef move_in(self, unsigned int duration, x, y, z, formula=None):
        self.offset_interpolator = Interpolator(self.dest_offset, self.frame,
                                                (x, y, z), self.frame + duration,
                                                formula)


    cpdef rotate_in(self, unsigned int duration, rx, ry, rz, formula=None):
        self.rotation_interpolator = Interpolator(self.rotations_3d, self.frame,
                                                  (rx, ry, rz), self.frame + duration,
                                                  formula)


    cpdef change_color_in(self, unsigned int duration, r, g, b, formula=None):
        self.color_interpolator = Interpolator(self.color, self.frame,
                                               (r, g, b), self.frame + duration,
                                               formula)


    cpdef update_orientation(self, double angle_base=0., bint force_rotation=False):
        if (self.angle != angle_base or self.force_rotation != force_rotation):
            self.angle = angle_base
            self.force_rotation = force_rotation
            self.changed = True


    cpdef Sprite copy(self):
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

        return sprite


    cpdef update(self):
        self.frame += 1

        sax, say, saz = self._rotations_speed_3d[0], self._rotations_speed_3d[1], self._rotations_speed_3d[2] #XXX
        if sax or say or saz:
            ax, ay, az = self._rotations_3d[0], self._rotations_3d[1], self._rotations_3d[2] #XXX
            self._rotations_3d[:] = [ax + sax, ay + say, az + saz]
            self.changed = True
        elif self.rotation_interpolator:
            self.rotation_interpolator.update(self.frame)
            self.rotations_3d = self.rotation_interpolator.values
            self.changed = True

        rsx, rsy = self._scale_speed[0], self._scale_speed[1] #XXX
        if rsx or rsy:
            rx, ry = self._rescale[0], self._rescale[1] #XXX
            self._rescale[:] = [rx + rsx, ry + rsy]
            self.changed = True

        if self.fade_interpolator:
            self.fade_interpolator.update(self.frame)
            self._color[3] = self.fade_interpolator.values[0]
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
