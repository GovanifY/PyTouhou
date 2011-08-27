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


from random import randrange

from pytouhou.utils.helpers import get_logger
from pytouhou.vm.common import MetaRegistry, instruction

logger = get_logger(__name__)


class ANMRunner(object):
    __metaclass__ = MetaRegistry
    __slots__ = ('_anm_wrapper', '_sprite', '_running',
                 'script', 'instruction_pointer', 'frame')


    def __init__(self, anm_wrapper, script_id, sprite):
        self._anm_wrapper = anm_wrapper
        self._sprite = sprite
        self._running = True

        anm, self.script = anm_wrapper.get_script(script_id)
        self.frame = 0
        self.instruction_pointer = 0
        pass


    def run_frame(self):
        if self._sprite._removed:
            return False

        while self._running:
            try:
                frame, instr_type, args = self.script[self.instruction_pointer]
            except IndexError:
                return False

            if frame > self.frame:
                break
            else:
                self.instruction_pointer += 1

            if frame == self.frame:
                try:
                    callback = self._handlers[instr_type]
                except KeyError:
                    logger.warn('unhandled opcode %d (args: %r)', instr_type, args)
                else:
                    callback(self, *args)
                    self._sprite._changed = True
        self.frame += 1
        return self._running


    @instruction(0)
    def remove(self):
        self._sprite._removed = True
        self._running = True


    @instruction(1)
    def load_sprite(self, sprite_index):
        self._sprite.anm, self._sprite.texcoords = self._anm_wrapper.get_sprite(sprite_index)


    @instruction(2)
    def set_scale(self, sx, sy):
        self._sprite.rescale = sx, sy


    @instruction(3)
    def set_alpha(self, alpha):
        self._sprite.alpha = alpha % 256 #TODO


    @instruction(4)
    def set_color(self, b, g, r):
        self._sprite.color = (r, g, b)


    @instruction(5)
    def jump(self, instruction_pointer):
        #TODO: is that really how it works?
        self.instruction_pointer = instruction_pointer
        self.frame = self.script[self.instruction_pointer][0]


    @instruction(7)
    def toggle_mirrored(self):
        self._sprite.mirrored = not self._sprite.mirrored


    @instruction(9)
    def set_rotations_3d(self, rx, ry, rz):
        self._sprite.rotations_3d = rx, ry, rz


    @instruction(10)
    def set_rotations_speed_3d(self, srx, sry, srz):
        self._sprite.rotations_speed_3d = srx, sry, srz


    @instruction(11)
    def set_scale_speed(self, ssx, ssy):
        self._sprite.scale_speed = ssx, ssy


    @instruction(12)
    def fade(self, new_alpha, duration):
        self._sprite.fade(duration, new_alpha, lambda x: x) #TODO: formula

    @instruction(15)
    @instruction(21) #TODO
    def keep_still(self):
        self._running = False

    @instruction(16)
    def load_random_sprite(self, min_idx, amp):
        #TODO: use the game's PRNG?
        self.load_sprite(min_idx + randrange(amp))


    @instruction(19)
    def move_in(self, x, y, z, duration):
        self._sprite.move_in(duration, x, y, z, lambda x: x) #TODO: formula


    @instruction(23)
    def set_corner_relative_placement(self):
        self._sprite.corner_relative_placement = True #TODO


    @instruction(25)
    def set_allow_dest_offset(self, value):
        self._sprite.allow_dest_offset = bool(value)


    @instruction(27)
    def shift_texture_x(self, dx):
        tox, toy = self._sprite.texoffsets
        self._sprite.texoffsets = tox + dx, toy


    @instruction(28)
    def shift_texture_y(self, dy):
        tox, toy = self._sprite.texoffsets
        self._sprite.texoffsets = tox, toy + dy


    @instruction(30)
    def scale_in(self, sx, sy, duration):
        self._sprite.scale_in(duration, sx, sy, lambda x: x) #TODO: formula
