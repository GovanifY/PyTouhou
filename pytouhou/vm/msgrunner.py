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
from pytouhou.game import NextStage

logger = get_logger(__name__)


class MSGRunner(metaclass=MetaRegistry):
    __slots__ = ('_msg', '_game', 'frame', 'sleep_time', 'allow_skip',
                 'skipping', 'frozen', 'ended', 'instruction_pointer',
                 'handlers')

    def __init__(self, msg, script, game):
        self._msg = msg.msgs[script + 10 * (game.players[0].character // 2)]
        self._game = game
        self.handlers = self._handlers[6]
        self.frame = 0
        self.sleep_time = 0
        self.allow_skip = True
        self.skipping = False
        self.frozen = False
        self.ended = False

        self.instruction_pointer = 0


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
                    callback = self.handlers[instr_type]
                except KeyError:
                    logger.warn('unhandled msg opcode %d (args: %r)', instr_type, args)
                else:
                    callback(self, *args)

        if not self.frozen:
            if self.sleep_time > 0:
                self.sleep_time -= 1
            else:
                self.frame += 1

        return True


    def skip(self):
        self.sleep_time = 0


    def end(self):
        self._game.msg_runner = None
        self._game.msg_wait = False
        self.ended = True
        texts = self._game.texts
        if 'boss_name' in texts:
            del texts['boss_name']
        if 'boss_title' in texts:
            del texts['boss_title']
        if 'dialog_0' in texts:
            del texts['dialog_0']
        if 'dialog_1' in texts:
            del texts['dialog_1']


    @instruction(0)
    def unknown0(self):
        if self.allow_skip:
            raise Exception #TODO: seems to crash the game, but why?
        self.end()


    @instruction(1)
    def enter(self, side, effect):
        self._game.new_face(side, effect)


    @instruction(2)
    def change_face(self, side, index):
        face = self._game.faces[side]
        if face:
            face.load(index)


    @instruction(3)
    def display_text(self, side, index, text):
        texts = self._game.texts
        if index == 0:
            if 'dialog_0' in texts:
                del texts['dialog_0']
            if 'dialog_1' in texts:
                del texts['dialog_1']
        texts['dialog_%d' % index] = self._game.new_native_text((64, 372 + index * 24), text)
        texts['dialog_%d' % index].set_timeout(0, effect='fadeout', duration=15)


    @instruction(4)
    def pause(self, duration):
        if not (self.skipping and self.allow_skip):
            self.sleep_time = duration


    @instruction(5)
    def animate(self, side, effect):
        face = self._game.faces[side]
        if face:
            face.animate(effect)


    @instruction(6)
    def spawn_enemy_sprite(self):
        self._game.msg_wait = False


    @instruction(7)
    def change_music(self, track):
        self._game.music.play(track)


    @instruction(8)
    def display_description(self, side, index, text):
        assert side == 1  # It shouldn’t crash when it’s something else.
        key = 'boss_name' if index == 0 else 'boss_title'
        self._game.texts[key] = self._game.new_native_text((336, 320 + index * 18), text, align='right')


    @instruction(10)
    def freeze(self):
        self.frozen = True


    @instruction(11)
    def next_stage(self):
        raise NextStage


    @instruction(13)
    def set_allow_skip(self, boolean):
        self.allow_skip = bool(boolean)
