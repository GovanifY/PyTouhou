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

from pytouhou.vm.anmrunner import ANMRunner


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

    def normal_update(self):
        if self.changed:
            if self.anmrunner is not None and not self.anmrunner.run_frame():
                self.anmrunner = None
            self.changed = False
        self.frame += 1



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


    def set_length(self, length):
        current_length = len(self.glyphes)
        if length > current_length:
            self.glyphes.extend([Glyph(self.ref_sprite.copy(),
                                       (self.x + self.xspacing * i, self.y))
                                 for i in range(current_length, length)])
            self.objects = [self] + self.glyphes
        elif length < current_length:
            self.glyphes[:] = self.glyphes[:length]
            self.objects = [self] + self.glyphes


    def set_sprites(self, sprite_indexes):
        self.set_length(len(sprite_indexes))
        for glyph, idx in zip(self.glyphes, sprite_indexes):
            glyph.sprite.anm = self.anm
            glyph.sprite.texcoords = self.anm.sprites[idx]
            glyph.sprite.changed = True


    def set_color(self, text=None, color=None):
        if text is not None:
            colors = {'white': (255, 255, 255), 'yellow': (255, 255, 0),
                      'blue': (192, 192, 255), 'darkblue': (160, 128, 255),
                      'purple': (224, 128, 255), 'red': (255, 64, 0)}
            color = colors[text]
        else:
            assert color is not None
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
        self.text = b''
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
        GlyphCollection.normal_update(self)
        if self.frame == self.timeout:
            self.removed = True


    def move_timeout_update(self):
        if self.frame % 2:
            for glyph in self.glyphes:
                glyph.y -= 1
        self.timeout_update()


    def fadeout_timeout_update(self):
        if self.frame >= self.start:
            if self.frame == self.start:
                self.fade(self.duration, 255)
            elif self.frame == self.timeout - self.duration:
                self.fade(self.duration, 0)
            self.fade_interpolator.update(self.frame)
            self.alpha = int(self.fade_interpolator.values[0])
            for glyph in self.glyphes:
                glyph.sprite.alpha = self.alpha
                glyph.sprite.changed = True
        self.timeout_update()


    def fade(self, duration, alpha, formula=None):
        self.fade_interpolator = Interpolator((self.alpha,), self.frame,
                                              (alpha,), self.frame + duration,
                                              formula)


    def set_timeout(self, timeout, effect=None, duration=0, start=0):
        self.timeout = timeout + start
        if effect == 'move':
            self.update = self.move_timeout_update
        elif effect == 'fadeout':
            self.alpha = 0
            for glyph in self.glyphes:
                glyph.sprite.alpha = 0
            self.update = self.fadeout_timeout_update
            self.duration = duration
            self.start = start
        else:
            self.update = self.timeout_update



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
        if self.anmrunner is not None and not self.anmrunner.run_frame():
            self.anmrunner = None



class NativeText(Element):
    def __init__(self, pos, text, gradient=None, alpha=255, shadow=False, align='left'):
        self.removed = False
        self.x, self.y = pos
        self.text = text
        self.alpha = alpha
        self.shadow = shadow
        self.align = align
        self.frame = 0

        self.gradient = gradient or [(255, 255, 255), (255, 255, 255),
                                     (128, 128, 255), (128, 128, 255)]

        self.update = self.normal_update


    def normal_update(self):
        self.frame += 1


    def timeout_update(self):
        self.normal_update()
        if self.frame == self.timeout:
            self.removed = True


    def move_timeout_update(self):
        if self.frame % 2:
            self.y -= 1
        self.timeout_update()


    def move_ex_timeout_update(self):
        if self.frame >= self.start:
            if self.frame == self.start:
                self.move_in(self.duration, self.to[0], self.to[1])
            elif self.frame == self.timeout - self.duration:
                self.move_in(self.duration, self.end[0], self.end[1])
            if self.offset_interpolator:
                self.offset_interpolator.update(self.frame)
                self.x, self.y = self.offset_interpolator.values
        self.timeout_update()


    def fadeout_timeout_update(self):
        if self.frame >= self.start:
            if self.frame == self.start:
                self.fade(self.duration, 255)
            elif self.frame == self.timeout - self.duration:
                self.fade(self.duration, 0)
            self.fade_interpolator.update(self.frame)
            self.alpha = int(self.fade_interpolator.values[0])
        self.timeout_update()


    def fade(self, duration, alpha, formula=None):
        self.fade_interpolator = Interpolator((self.alpha,), self.frame,
                                              (alpha,), self.frame + duration,
                                              formula)


    def move_in(self, duration, x, y, formula=None):
        self.offset_interpolator = Interpolator((self.x, self.y), self.frame,
                                                (x, y), self.frame + duration,
                                                formula)


    def set_timeout(self, timeout, effect=None, duration=0, start=0, to=None, end=None):
        self.timeout = timeout + start
        if effect == 'move':
            self.update = self.move_timeout_update
        elif effect == 'move_ex':
            self.update = self.move_ex_timeout_update
            self.duration = duration
            self.start = start
            self.to[:] = [to[0], to[1]]
            self.end[:] = [end[0], end[1]]
        elif effect == 'fadeout':
            self.alpha = 0
            self.update = self.fadeout_timeout_update
            self.duration = duration
            self.start = start
        else:
            self.update = self.timeout_update
