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


from random import randrange, random

from pytouhou.utils.helpers import get_logger
from pytouhou.vm.common import MetaRegistry, instruction

logger = get_logger(__name__)


class ANMRunner(metaclass=MetaRegistry):
    __slots__ = ('_anm', '_sprite', 'running', 'sprite_index_offset', 'script',
                 'instruction_pointer', 'frame', 'waiting', 'handlers',
                 'variables', 'version', 'timeout')

    #TODO: check!
    formulae = {0: None,
                1: lambda x: x ** 2,
                2: lambda x: x ** 3,
                3: lambda x: x ** 4,
                4: lambda x: 2 * x - x ** 2,
                5: lambda x: 2 * x - x ** 3,
                6: lambda x: 2 * x - x ** 4,
                7: None,
                255: None} #XXX

    def __init__(self, anm, script_id, sprite, sprite_index_offset=0):
        self._anm = anm
        self._sprite = sprite
        self.running = True
        self.waiting = False

        self.script = anm.scripts[script_id]
        self.version = anm.version
        self.handlers = self._handlers[{0: 6, 2: 7}[anm.version]]
        self.frame = 0
        self.timeout = -1
        self.instruction_pointer = 0
        self.variables = [0,  0,  0,  0,
                          0., 0., 0., 0.,
                          0,  0,  0,  0]

        self.sprite_index_offset = sprite_index_offset
        self.run_frame()
        self.sprite_index_offset = 0


    def interrupt(self, interrupt):
        new_ip = self.script.interrupts.get(interrupt, None)
        if new_ip is None:
            new_ip = self.script.interrupts.get(-1, None)
        if new_ip is None:
            return False
        self.instruction_pointer = new_ip
        self.frame, opcode, args = self.script[self.instruction_pointer]
        self.waiting = False
        self._sprite.visible = True
        return True


    def run_frame(self):
        if not self.running:
            return False

        while self.running and not self.waiting:
            frame, opcode, args = self.script[self.instruction_pointer]

            if frame > self.frame:
                break
            else:
                self.instruction_pointer += 1

            if frame == self.frame:
                try:
                    callback = self.handlers[opcode]
                except KeyError:
                    logger.debug('[%d - %04d] unhandled opcode %d (args: %r)',
                                 id(self), self.frame, opcode, args)
                else:
                    callback(self, *args)
                    self._sprite.changed = True

        if not self.waiting:
            self.frame += 1
        elif self.timeout == self._sprite.frame: #TODO: check if it’s happening at the correct frame.
            self.waiting = False

        self._sprite.update()

        return self.running


    def _setval(self, variable_id, value):
        if self.version == 2:
            if 10000 <= variable_id <= 10011:
                self.variables[int(variable_id-10000)] = value


    def _getval(self, value):
        if self.version == 2:
            if 10000 <= value <= 10011:
                return self.variables[int(value-10000)]
        return value


    @instruction(0)
    @instruction(1, 7)
    def remove(self):
        self._sprite.removed = True
        self.running = False


    @instruction(1)
    @instruction(3, 7)
    def load_sprite(self, sprite_index):
        #TODO: version 2 only: do not crash when assigning a non-existant sprite.
        self._sprite.anm, self._sprite.texcoords = self._anm, self._anm.sprites[sprite_index + self.sprite_index_offset]


    @instruction(2)
    @instruction(7, 7)
    def set_scale(self, sx, sy):
        self._sprite.rescale = self._getval(sx), self._getval(sy)


    @instruction(3)
    @instruction(8, 7)
    def set_alpha(self, alpha):
        self._sprite.alpha = alpha % 256 #TODO


    @instruction(4)
    @instruction(9, 7)
    def set_color(self, b, g, r):
        if not self._sprite.fade_interpolator:
            self._sprite.color = (r, g, b)


    @instruction(5)
    def jump(self, instruction_pointer):
        #TODO: is that really how it works?
        self.instruction_pointer = instruction_pointer
        self.frame = self.script[self.instruction_pointer][0]


    @instruction(7)
    @instruction(10, 7)
    def toggle_mirrored(self):
        self._sprite.mirrored = not self._sprite.mirrored


    @instruction(9)
    @instruction(12, 7)
    def set_rotations_3d(self, rx, ry, rz):
        self._sprite.rotations_3d = self._getval(rx), self._getval(ry), self._getval(rz)


    @instruction(10)
    @instruction(13, 7)
    def set_rotations_speed_3d(self, srx, sry, srz):
        self._sprite.rotations_speed_3d = self._getval(srx), self._getval(sry), self._getval(srz)


    @instruction(11)
    @instruction(14, 7)
    def set_scale_speed(self, ssx, ssy):
        self._sprite.scale_speed = ssx, ssy


    @instruction(12)
    @instruction(15, 7)
    def fade(self, new_alpha, duration):
        self._sprite.fade(duration, new_alpha)


    @instruction(13)
    def set_blendfunc_alphablend(self):
        self._sprite.blendfunc = 1


    @instruction(14)
    def set_blendfunc_add(self):
        self._sprite.blendfunc = 0 #TODO


    @instruction(15)
    @instruction(2, 7)
    def keep_still(self):
        self.running = False

    @instruction(16)
    def load_random_sprite(self, min_idx, amp):
        #TODO: use the game's PRNG?
        self.load_sprite(min_idx + randrange(amp))


    @instruction(17)
    @instruction(6, 7)
    def move(self, x, y, z):
        self._sprite.dest_offset = (x, y, z)


    @instruction(18)
    @instruction(17, 7)
    def move_in_linear(self, x, y, z, duration):
        self._sprite.move_in(duration, x, y, z)


    @instruction(19)
    @instruction(18, 7)
    def move_in_decel(self, x, y, z, duration):
        self._sprite.move_in(duration, x, y, z, lambda x: 2. * x - x ** 2)


    @instruction(20)
    @instruction(19, 7)
    def move_in_accel(self, x, y, z, duration):
        self._sprite.move_in(duration, x, y, z, lambda x: x ** 2)


    @instruction(21)
    @instruction(20, 7)
    def wait(self):
        """Wait for an interrupt.
        """
        self.waiting = True


    @instruction(22)
    @instruction(21, 7)
    def interrupt_label(self, interrupt):
        """Noop"""
        pass


    @instruction(23)
    @instruction(22, 7)
    def set_corner_relative_placement(self):
        self._sprite.corner_relative_placement = True #TODO


    @instruction(24)
    @instruction(23, 7)
    def wait_ex(self):
        """Hide the sprite and wait for an interrupt.
        """
        self._sprite.visible = False
        self.waiting = True


    @instruction(25)
    @instruction(24, 7)
    def set_allow_dest_offset(self, value):
        self._sprite.allow_dest_offset = bool(value)


    @instruction(26)
    @instruction(25, 7)
    def set_automatic_orientation(self, value):
        """If true, rotate by pi-angle around the z axis.
        """
        self._sprite.automatic_orientation = bool(value)


    @instruction(27)
    @instruction(26, 7)
    def shift_texture_x(self, dx):
        tox, toy = self._sprite.texoffsets
        self._sprite.texoffsets = tox + dx, toy


    @instruction(28)
    @instruction(27, 7)
    def shift_texture_y(self, dy):
        tox, toy = self._sprite.texoffsets
        self._sprite.texoffsets = tox, toy + dy


    @instruction(29)
    @instruction(28, 7)
    def set_visible(self, visible):
        self._sprite.visible = bool(visible & 1)


    @instruction(30)
    @instruction(29, 7)
    def scale_in(self, sx, sy, duration):
        self._sprite.scale_in(duration, sx, sy)


# Now are the instructions new to anm2.


    @instruction(0, 7)
    def noop(self):
        pass


    @instruction(4, 7)
    def jump_bis(self, instruction_pointer, frame):
        self.instruction_pointer = instruction_pointer
        self.frame = frame


    @instruction(5, 7)
    def jump_ex(self, variable_id, instruction_pointer, frame):
        """If the given variable is non-zero, decrease it by 1 and jump to a
        relative offset in the same subroutine.
        """
        counter_value = self._getval(variable_id) - 1
        if counter_value > 0:
            self._setval(variable_id, counter_value)
            self.instruction_pointer = instruction_pointer
            self.frame = frame


    @instruction(16, 7)
    def set_blendfunc(self, value):
        self._sprite.blendfunc = bool(value & 1)


    @instruction(32, 7)
    def move_in_bis(self, duration, formula, x, y, z):
        self._sprite.move_in(duration, x, y, z, self.formulae[formula])


    @instruction(33, 7)
    def change_color_in(self, duration, formula, r, g, b):
        self._sprite.change_color_in(duration, r, g, b, self.formulae[formula])


    @instruction(34, 7)
    def fade_bis(self, duration, formula, new_alpha):
        self._sprite.fade(duration, new_alpha, self.formulae[formula])


    @instruction(35, 7)
    def rotate_in_bis(self, duration, formula, rx, ry, rz):
        self._sprite.rotate_in(duration, rx, ry, rz, self.formulae[formula])


    @instruction(36, 7)
    def scale_in_bis(self, duration, formula, sx, sy):
        self._sprite.scale_in(duration, sx, sy, self.formulae[formula])


    @instruction(37, 7)
    @instruction(38, 7)
    def set_variable(self, variable_id, value):
        self._setval(variable_id, value)


    @instruction(42, 7)
    def decrement(self, variable_id, value):
        self._setval(variable_id, self._getval(variable_id) - self._getval(value))


    @instruction(50, 7)
    def add(self, variable_id, a, b):
        self._setval(variable_id, self._getval(a) + self._getval(b))


    @instruction(52, 7)
    def substract(self, variable_id, a, b):
        self._setval(variable_id, self._getval(a) - self._getval(b))


    @instruction(55, 7)
    def divide_int(self, variable_id, a, b):
        self._setval(variable_id, self._getval(a) // self._getval(b))


    @instruction(59, 7)
    def set_random_int(self, variable_id, amp):
        #TODO: use the game's PRNG?
        self._setval(variable_id, randrange(amp))


    @instruction(60, 7)
    def set_random_float(self, variable_id, amp):
        #TODO: use the game's PRNG?
        self._setval(variable_id, amp * random())


    @instruction(69, 7)
    def branch_if_not_equal(self, variable_id, value, instruction_pointer, frame):
        if self._getval(variable_id) != value:
            self.instruction_pointer = instruction_pointer
            self.frame = frame
            assert self.frame == self.script[self.instruction_pointer][0]


    @instruction(79, 7)
    def wait_duration(self, duration):
        self.timeout = self._sprite.frame + duration
        self.waiting = True
