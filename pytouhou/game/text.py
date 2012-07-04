# -*- encoding: utf-8 -*-
##
## Copyright (C) 2011 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from copy import copy

from pytouhou.game.sprite import Sprite
from pytouhou.vm.anmrunner import ANMRunner


class Glyph(object):
    def __init__(self, sprite, pos):
        self.sprite = sprite
        self.removed = False

        self.x, self.y = pos


class Widget(object):
    def __init__(self, pos, back_wrapper=None):
        self.sprite = None
        self.removed = False
        self.changed = True
        self.anmrunner = None

        # Set up the backround sprite
        self.back_wrapper = back_wrapper
        if back_wrapper:
            self.sprite = Sprite()
            self.anmrunner = ANMRunner(back_wrapper, 22, self.sprite)
            self.anmrunner.run_frame()

        self.x, self.y = pos

    def update(self):
        if self.changed:
            if self.anmrunner and not self.anmrunner.run_frame():
                self.anmrunner = None
            self.changed = False



class GlyphCollection(Widget):
    def __init__(self, pos, anm_wrapper, back_wrapper=None, ref_script=0, xspacing=14):
        Widget.__init__(self, pos, back_wrapper)

        self.ref_sprite = Sprite()
        self.anm_wrapper = anm_wrapper
        self.glyphes = []
        self.xspacing = xspacing

        # Set up ref sprite
        anm_runner = ANMRunner(anm_wrapper, ref_script, self.ref_sprite)
        anm_runner.run_frame()
        self.ref_sprite.corner_relative_placement = True #TODO: perhaps not right


    def objects(self):
        return self.glyphes


    def set_length(self, length):
        current_length = len(self.glyphes)
        if length > current_length:
            self.glyphes.extend(Glyph(copy(self.ref_sprite),
                                      (self.x + self.xspacing * i, self.y))
                                        for i in range(current_length, length))
        elif length < current_length:
            self.glyphes[:] = self.glyphes[:length]


    def set_sprites(self, sprite_indexes):
        self.set_length(len(sprite_indexes))
        for glyph, idx in zip(self.glyphes, sprite_indexes):
            glyph.sprite.anm, glyph.sprite.texcoords = self.anm_wrapper.get_sprite(idx)
            glyph.sprite.changed = True



class Text(GlyphCollection):
    def __init__(self, pos, ascii_wrapper, back_wrapper=None, text='', xspacing=14, shift=21):
        GlyphCollection.__init__(self, pos, ascii_wrapper, back_wrapper, xspacing=xspacing)
        self.text = ''
        self.shift = shift

        self.set_text(text)


    def set_text(self, text):
        if text == self.text:
            return

        self.set_sprites([ord(c) - self.shift for c in text])
        self.text = text
        self.changed = True


    def set_color(self, color):
        colors = {'white': (255, 255, 255), 'yellow': (255, 255, 0), 'blue': (192, 192, 255), 'darkblue': (160, 128, 255), 'purple': (224, 128, 255), 'red': (255, 64, 0)}
        self.ref_sprite.color = colors[color]
        for glyph in self.glyphes:
            glyph.sprite.color = colors[color]


    def timeout_update(self):
        GlyphCollection.update(self)
        if self.timeout % 2:
            for glyph in self.glyphes:
                glyph.y -= 1
        self.timeout -= 1
        if self.timeout == 0:
            self.removed = True


    def set_timeout(self, timeout):
        self.timeout = timeout
        self.update = self.timeout_update



class Counter(GlyphCollection):
    def __init__(self, pos, anm_wrapper, back_wrapper=None, script=0, xspacing=16, value=0):
        GlyphCollection.__init__(self, pos,
                                 anm_wrapper, back_wrapper=back_wrapper,
                                 ref_script=script, xspacing=xspacing)

        self.value = value
        self.set_value(value)


    def set_value(self, value):
        if value < 0:
            value = 0
        if value == self.value:
            return

        self.set_length(value)
        self.value = value
        self.changed = True



class Gauge(object):
    def __init__(self, pos, anm_wrapper, max_length=280, maximum=1, value=0):
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(anm_wrapper, 21, self.sprite)
        self.anmrunner.run_frame()
        self.removed = False
        self.sprite.corner_relative_placement = True #TODO: perhaps not right

        self.x, self.y = pos
        self.max_length = max_length
        self.maximum = maximum

        self.set_value(value)


    def set_value(self, value):
        self.value = value
        self.sprite.width_override = self.max_length * value / self.maximum
        self.sprite.changed = True #TODO


    def update(self):
        #XXX
        if self.value == 0:
            self.sprite.visible = False
        else:
            self.sprite.visible = True
        if self.anmrunner and not self.anmrunner.run_frame():
            self.anmrunner = None


