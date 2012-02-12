# -*- encoding: utf-8 -*-
##
## Copyright (C) 2012 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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


from pytouhou.utils.helpers import get_logger

from pytouhou.vm.common import MetaRegistry, instruction
from pytouhou.game.face import Face

logger = get_logger(__name__)


class MSGRunner(object):
    __metaclass__ = MetaRegistry
    __slots__ = ('_msg', '_game', 'frame', 'sleep_time', 'allow_skip',
                 'frozen', 'faces', 'ended', 'instruction_pointer')

    def __init__(self, msg, script, game):
        self._msg = msg.msgs[script + 10 * (game.players[0].state.character // 2)]
        self._game = game
        self.frame = 0
        self.sleep_time = 0
        self.allow_skip = True
        self.frozen = False

        self.faces = [None, None]
        game.msg_sprites = self.objects
        self.ended = False

        self.instruction_pointer = 0


    def objects(self):
        return [face for face in self.faces if face] if not self.ended else []


    def run_iteration(self):
        while True:
            if self.ended:
                return False

            try:
                frame, instr_type, args = self._msg[self.instruction_pointer]
            except IndexError:
                self.end()
                return False

            if frame > self.frame:
                break
            else:
                self.instruction_pointer += 1

            if frame == self.frame:
                try:
                    callback = self._handlers[instr_type]
                except KeyError:
                    logger.warn('unhandled msg opcode %d (args: %r)', instr_type, args)
                else:
                    callback(self, *args)

        if not self.frozen:
            if self.sleep_time > 0:
                self.sleep_time -= 1
            else:
                self.frame += 1

        for face in self.faces:
            if face:
                face.update()

        return True


    def skip(self):
        self.sleep_time = 0


    def end(self):
        self._game.msg_runner = None
        self._game.msg_wait = False
        self.ended = True


    @instruction(0)
    def unknown0(self):
        if self.allow_skip:
            raise Exception #TODO: seems to crash the game, but why?
        self.end()


    @instruction(1)
    def enter(self, side, effect):
        self.faces[side] = Face(self._game.msg_anm_wrapper, effect, side)


    @instruction(2)
    def change_face(self, side, index):
        face = self.faces[side]
        if face:
            face.load(index)


    @instruction(4)
    def pause(self, duration):
        self.sleep_time = duration


    @instruction(5)
    def animate(self, side, effect):
        face = self.faces[side]
        if face:
            face.animate(effect)


    @instruction(6)
    def spawn_enemy_sprite(self):
        self._game.msg_wait = False


    @instruction(10)
    def freeze(self):
        self.frozen = True


    @instruction(13)
    def set_allow_skip(self, boolean):
        self.allow_skip = bool(boolean)
