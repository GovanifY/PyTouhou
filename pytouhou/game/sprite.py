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


from struct import unpack

from pytouhou.utils.matrix import Matrix


class AnmWrapper(object):
    def __init__(self, anm_files):
        self.anm_files = list(anm_files)

    def get_sprite(self, script_index):
        for anm in self.anm_files:
            if script_index in anm.scripts:
                return anm, Sprite(anm, script_index)



class Sprite(object):
    def __init__(self, anm, script_index):
        self.anm = anm
        self.script_index = script_index
        self.texcoords = (0, 0, 0, 0) # x, y, width, height
        self.texoffsets = (0., 0.)
        self.mirrored = False
        self.rescale = (1., 1.)
        self.rotations_3d = (0., 0., 0.)
        self.rotations_speed_3d = (0., 0., 0.)
        self.corner_relative_placement = False
        self.instruction_pointer = 0
        self.keep_still = False
        self.playing = True
        self.frame = 0
        self.alpha = 255
        self._uvs = []
        self._vertices = []
        self._colors = []


    def update_vertices_uvs_colors(self, override_width=0, override_height=0):
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

        x_1 = 1. / self.anm.size[0]
        y_1 = 1. / self.anm.size[1]
        tox, toy = self.texoffsets
        uvs = [(tx * x_1 + tox,         1. - (ty * y_1) + toy),
               ((tx + tw) * x_1 + tox,  1. - (ty * y_1) + toy),
               ((tx + tw) * x_1 + tox,  1. - ((ty + th) * y_1 + toy)),
               (tx * x_1 + tox,         1. - ((ty + th) * y_1 + toy))]

        d = vertmat.data
        assert (d[3][0], d[3][1], d[3][2], d[3][3]) == (1., 1., 1., 1.)
        self._colors = [(255, 255, 255, self.alpha)] * 4
        self._uvs, self._vertices = uvs, zip(d[0], d[1], d[2])



    def update(self):
        if not self.playing:
            return False

        changed = False
        if not self.keep_still:
            script = self.anm.scripts[self.script_index]
            frame = self.frame
            while True:
                try:
                    frame, instr_type, args = script[self.instruction_pointer]
                except IndexError:
                    self.playing = False
                    return False

                if frame > self.frame:
                    break
                else:
                    self.instruction_pointer += 1
                if frame == self.frame:
                    changed = True
                    if instr_type == 0:
                        self.playing = False
                        return False
                    if instr_type == 1:
                        self.texcoords = self.anm.sprites[args[0]]
                    elif instr_type == 2:
                        self.rescale = args
                    elif instr_type == 3:
                        self.alpha = args[0] % 256 #TODO
                    elif instr_type == 5:
                        self.instruction_pointer, = args
                        self.frame = script[self.instruction_pointer][0]
                    elif instr_type == 7:
                        self.mirrored = True
                    elif instr_type == 9:
                        self.rotations_3d = args
                    elif instr_type == 10:
                        self.rotations_speed_3d = args
                    elif instr_type == 23:
                        self.corner_relative_placement = True #TODO
                    elif instr_type == 27:
                        tox, toy = self.texoffsets
                        self.texoffsets = tox + args[0], toy
                    elif instr_type == 28:
                        tox, toy = self.texoffsets
                        self.texoffsets = tox, toy + args[0]
                    elif instr_type == 15:
                        self.keep_still = True
                        break
                    else:
                        print('unhandled opcode: %d, %r' % (instr_type, args)) #TODO
        self.frame += 1

        ax, ay, az = self.rotations_3d
        sax, say, saz = self.rotations_speed_3d
        self.rotations_3d = ax + sax, ay + say, az + saz

        if self.rotations_speed_3d != (0., 0., 0.):
            return True

        return changed

