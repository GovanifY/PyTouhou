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

from pytouhou.game.element import Element
from pytouhou.game.sprite import Sprite
from pytouhou.vm.anmrunner import ANMRunner
from pytouhou.utils.interpolator import Interpolator


class Glyph(Element):
    def __init__(self, sprite, pos):
        Element.__init__(self, pos)
        self.sprite = sprite


class Widget(Element):
    def __init__(self, pos, back_anm=None, back_script=22):
        Element.__init__(self, pos)
        self.changed = True
        self.frame = 0

        # Set up the backround sprite
        self.back_anm = back_anm
        if back_anm:
            self.sprite = Sprite()
            self.anmrunner = ANMRunner(back_anm, back_script, self.sprite)

    def update(self):
        self.frame += 1
        if self.changed:
            if self.anmrunner and not self.anmrunner.run_frame():
                self.anmrunner = None
            self.changed = False



class GlyphCollection(Widget):
    def __init__(self, pos, anm, back_anm=None, ref_script=0,
                 xspacing=14, back_script=22):
        Widget.__init__(self, pos, back_anm, back_script)

        self.ref_sprite = Sprite()
        self.anm = anm
        self.glyphes = []
        self.xspacing = xspacing

        # Set up ref sprite
        ANMRunner(anm, ref_script, self.ref_sprite)
        self.ref_sprite.corner_relative_placement = True #TODO: perhaps not right


    @property
    def objects(self):
        return [self] + self.glyphes


    def set_length(self, length):
        current_length = len(self.glyphes)
        if length > current_length:
            self.glyphes.extend(Glyph(self.ref_sprite.copy(),
                                      (self.x + self.xspacing * i, self.y))
                                for i in range(current_length, length))
        elif length < current_length:
            self.glyphes[:] = self.glyphes[:length]


    def set_sprites(self, sprite_indexes):
        self.set_length(len(sprite_indexes))
        for glyph, idx in zip(self.glyphes, sprite_indexes):
            glyph.sprite.anm = self.anm
            glyph.sprite.texcoords = self.anm.sprites[idx]
            glyph.sprite.changed = True


    def set_color(self, color, text=True):
        if text:
            colors = {'white': (255, 255, 255), 'yellow': (255, 255, 0),
                      'blue': (192, 192, 255), 'darkblue': (160, 128, 255),
                      'purple': (224, 128, 255), 'red': (255, 64, 0)}
            color = colors[color]
        self.ref_sprite.color = color
        for glyph in self.glyphes:
            glyph.sprite.color = color


    def set_alpha(self, alpha):
        self.ref_sprite.alpha = alpha
        for glyph in self.glyphes:
            glyph.sprite.alpha = alpha



class Text(GlyphCollection):
    def __init__(self, pos, ascii_anm, back_anm=None, text='',
                 xspacing=14, shift=21, back_script=22, align='left'):
        GlyphCollection.__init__(self, pos, ascii_anm, back_anm,
                                 xspacing=xspacing, back_script=back_script)
        self.text = ''
        self.shift = shift

        if align == 'center':
            self.x -= xspacing * len(text) // 2
        elif align == 'right':
            self.x -= xspacing * len(text)
        else:
            assert align == 'left'

        self.set_text(text)


    def set_text(self, text):
        if text == self.text:
            return

        self.set_sprites([ord(c) - self.shift for c in text])
        self.text = text
        self.changed = True


    def timeout_update(self):
        GlyphCollection.update(self)
        if self.frame == self.timeout:
            self.removed = True


    def move_timeout_update(self):
        GlyphCollection.update(self)
        if self.frame % 2:
            for glyph in self.glyphes:
                glyph.y -= 1
        if self.frame == self.timeout:
            self.removed = True


    def fadeout_timeout_update(self):
        GlyphCollection.update(self)
        if self.frame >= self.start:
            if self.frame == self.start:
                self.fade(self.duration, 255, lambda x: x)
            elif self.frame == self.timeout - self.duration:
                self.fade(self.duration, 0, lambda x: x)
            if self.fade_interpolator:
                self.fade_interpolator.update(self.frame)
                self.alpha = int(self.fade_interpolator.values[0])
                for glyph in self.glyphes:
                    glyph.sprite.alpha = self.alpha
                    glyph.sprite.changed = True
        if self.frame == self.timeout:
            self.removed = True


    def fade(self, duration, alpha, formula):
        self.fade_interpolator = Interpolator((self.alpha,), self.frame,
                                              (alpha,), self.frame + duration,
                                              formula)


    def set_timeout(self, timeout, effect=None, duration=0, start=0):
        if effect == 'move':
            self.update = self.move_timeout_update
            self.timeout = timeout + start
        elif effect == 'fadeout':
            self.alpha = 0
            for glyph in self.glyphes:
                glyph.sprite.alpha = 0
            self.update = self.fadeout_timeout_update
            self.duration = duration
            self.start = start
            self.timeout = timeout + start
        else:
            self.update = self.timeout_update
            self.timeout = timeout + start



class Counter(GlyphCollection):
    def __init__(self, pos, anm, back_anm=None, script=0,
                 xspacing=16, value=0, back_script=22):
        GlyphCollection.__init__(self, pos, anm,
                                 back_anm=back_anm, ref_script=script,
                                 xspacing=xspacing, back_script=back_script)

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



class Gauge(Element):
    def __init__(self, pos, anm, max_length=280, maximum=1, value=0):
        Element.__init__(self, pos)
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(anm, 21, self.sprite)
        self.sprite.corner_relative_placement = True #TODO: perhaps not right

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


