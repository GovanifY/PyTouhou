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
    __slots__ = ('_anm_wrapper', '_sprite', 'running',
                 'sprite_index_offset',
                 'script', 'instruction_pointer', 'frame',
                 'waiting')


    def __init__(self, anm_wrapper, script_id, sprite, sprite_index_offset=0):
        self._anm_wrapper = anm_wrapper
        self._sprite = sprite
        self.running = True
        self.waiting = False

        anm, self.script = anm_wrapper.get_script(script_id)
        self.frame = 0
        self.instruction_pointer = 0

        self.sprite_index_offset = sprite_index_offset


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

        sprite = self._sprite

        while self.running and not self.waiting:
            frame, opcode, args = self.script[self.instruction_pointer]

            if frame > self.frame:
                break
            else:
                self.instruction_pointer += 1

            if frame == self.frame:
                try:
                    callback = self._handlers[opcode]
                except KeyError:
                    logger.warn('unhandled opcode %d (args: %r)', opcode, args)
                else:
                    callback(self, *args)
                    sprite.changed = True

        if not self.waiting:
            self.frame += 1

        # Update sprite
        sprite.frame += 1

        if sprite.rotations_speed_3d != (0., 0., 0.):
            ax, ay, az = sprite.rotations_3d
            sax, say, saz = sprite.rotations_speed_3d
            sprite.rotations_3d = ax + sax, ay + say, az + saz
            sprite.changed = True

        if sprite.scale_speed != (0., 0.):
            rx, ry = sprite.rescale
            rsx, rsy = sprite.scale_speed
            sprite.rescale = rx + rsx, ry + rsy
            sprite.changed = True

        if sprite.fade_interpolator:
            sprite.fade_interpolator.update(sprite.frame)
            sprite.alpha = int(sprite.fade_interpolator.values[0])
            sprite.changed = True

        if sprite.scale_interpolator:
            sprite.scale_interpolator.update(sprite.frame)
            sprite.rescale = sprite.scale_interpolator.values
            sprite.changed = True

        if sprite.offset_interpolator:
            sprite.offset_interpolator.update(sprite.frame)
            sprite.dest_offset = sprite.offset_interpolator.values
            sprite.changed = True

        return self.running


    @instruction(0)
    def remove(self):
        self._sprite.removed = True
        self.running = False


    @instruction(1)
    def load_sprite(self, sprite_index):
        self._sprite.anm, self._sprite.texcoords = self._anm_wrapper.get_sprite(sprite_index + self.sprite_index_offset)


    @instruction(2)
    def set_scale(self, sx, sy):
        self._sprite.rescale = sx, sy


    @instruction(3)
    def set_alpha(self, alpha):
        self._sprite.alpha = alpha % 256 #TODO


    @instruction(4)
    def set_color(self, b, g, r):
        if not self._sprite.fade_interpolator:
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


    @instruction(13)
    def set_blendfunc_alphablend(self):
        self._sprite.blendfunc = 1


    @instruction(14)
    def set_blendfunc_add(self):
        self._sprite.blendfunc = 0 #TODO


    @instruction(15)
    def keep_still(self):
        self.running = False

    @instruction(16)
    def load_random_sprite(self, min_idx, amp):
        #TODO: use the game's PRNG?
        self.load_sprite(min_idx + randrange(amp))


    @instruction(17)
    def move(self, x, y, z):
        self._sprite.dest_offset = (x, y, z)


    @instruction(18)
    def move_in_linear(self, x, y, z, duration):
        self._sprite.move_in(duration, x, y, z, lambda x: x)


    @instruction(19)
    def move_in_decel(self, x, y, z, duration):
        self._sprite.move_in(duration, x, y, z, lambda x: 2. * x - x ** 2)


    @instruction(20)
    def move_in_accel(self, x, y, z, duration):
        self._sprite.move_in(duration, x, y, z, lambda x: x ** 2)


    @instruction(21)
    def wait(self):
        """Wait for an interrupt.
        """
        self.waiting = True


    @instruction(22)
    def interrupt_label(self, interrupt):
        """Noop"""
        pass


    @instruction(23)
    def set_corner_relative_placement(self):
        self._sprite.corner_relative_placement = True #TODO


    @instruction(24)
    def wait_ex(self):
        """Hide the sprite and wait for an interrupt.
        """
        self._sprite.visible = False
        self.waiting = True


    @instruction(25)
    def set_allow_dest_offset(self, value):
        self._sprite.allow_dest_offset = bool(value)


    @instruction(26)
    def set_automatic_orientation(self, value):
        """If true, rotate by pi-angle around the z axis.
        """
        self._sprite.automatic_orientation = bool(value)


    @instruction(27)
    def shift_texture_x(self, dx):
        tox, toy = self._sprite.texoffsets
        self._sprite.texoffsets = tox + dx, toy


    @instruction(28)
    def shift_texture_y(self, dy):
        tox, toy = self._sprite.texoffsets
        self._sprite.texoffsets = tox, toy + dy


    @instruction(29)
    def set_visible(self, visible):
        self._sprite.visible = bool(visible & 1)


    @instruction(30)
    def scale_in(self, sx, sy, duration):
        self._sprite.scale_in(duration, sx, sy, lambda x: x) #TODO: formula

