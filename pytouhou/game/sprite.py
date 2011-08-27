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


from pytouhou.utils.matrix import Matrix
from pytouhou.utils.interpolator import Interpolator


class AnmWrapper(object):
    def __init__(self, anm_files):
        self.anm_files = list(anm_files)


    def get_sprite(self, sprite_index):
        for anm in self.anm_files:
            if sprite_index in anm.sprites:
                return anm, anm.sprites[sprite_index]
        raise IndexError


    def get_script(self, script_index):
        for anm in self.anm_files:
            if script_index in anm.scripts:
                return anm, anm.scripts[script_index]
        raise IndexError



class Sprite(object):
    def __init__(self):
        self.anm = None
        self._removed = False
        self._changed = False

        self.scale_interpolator = None
        self.fade_interpolator = None
        self.offset_interpolator = None

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
        self._uvs = []
        self._vertices = []
        self._colors = []


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


    def update_vertices_uvs_colors(self, override_width=0, override_height=0):
        if self.fade_interpolator:
            self.fade_interpolator.update(self.frame)
            self.alpha = int(self.fade_interpolator.values[0])

        if self.scale_interpolator:
            self.scale_interpolator.update(self.frame)
            self.rescale = self.scale_interpolator.values

        if self.offset_interpolator:
            self.offset_interpolator.update(self.frame)
            self.dest_offset = self.offset_interpolator.values


        vertmat = Matrix([[-.5,     .5,     .5,    -.5],
                          [-.5,    -.5,     .5,     .5],
                          [ .0,     .0,     .0,     .0],
                          [ 1.,     1.,     1.,     1.]])

        tx, ty, tw, th = self.texcoords
        sx, sy = self.rescale
        width = override_width or (tw * sx)
        height = override_height or (th * sy)

        vertmat.scale2d(width, height)
        if self.mirrored:
            vertmat.flip()
        if self.rotations_3d != (0., 0., 0.):
            rx, ry, rz = self.rotations_3d
            if rx:
                vertmat.rotate_x(-rx)
            if ry:
                vertmat.rotate_y(ry)
            if rz:
                vertmat.rotate_z(-rz) #TODO: minus, really?
        if self.corner_relative_placement: # Reposition
            vertmat.translate(width / 2., height / 2., 0.)
        if self.allow_dest_offset:
            vertmat.translate(*self.dest_offset)

        x_1 = 1. / self.anm.size[0]
        y_1 = 1. / self.anm.size[1]
        tox, toy = self.texoffsets
        uvs = [(tx * x_1 + tox,         1. - (ty * y_1) + toy),
               ((tx + tw) * x_1 + tox,  1. - (ty * y_1) + toy),
               ((tx + tw) * x_1 + tox,  1. - ((ty + th) * y_1 + toy)),
               (tx * x_1 + tox,         1. - ((ty + th) * y_1 + toy))]

        d = vertmat.data
        assert (d[3][0], d[3][1], d[3][2], d[3][3]) == (1., 1., 1., 1.)
        self._colors = [(self.color[0], self.color[1], self.color[2], self.alpha)] * 4
        self._uvs, self._vertices = uvs, zip(d[0], d[1], d[2])


    def update(self):
        if self.rotations_speed_3d != (0., 0., 0.) or self.scale_speed != (0., 0.):
            ax, ay, az = self.rotations_3d
            sax, say, saz = self.rotations_speed_3d
            self.rotations_3d = ax + sax, ay + say, az + saz
            self.rescale = self.rescale[0] + self.scale_speed[0], self.rescale[1] + self.scale_speed[1]
            self._changed = True
        self.frame += 1

