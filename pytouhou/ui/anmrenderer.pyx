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

from pytouhou.lib.opengl cimport \
         (glClearColor, glClear, GL_COLOR_BUFFER_BIT)

from pytouhou.game.sprite import Sprite
from pytouhou.vm import ANMRunner

from pytouhou.utils.helpers import get_logger
from pytouhou.utils.maths cimport perspective, setup_camera

from .renderer import Renderer
from .shaders.eosd import GameShader

cimport pytouhou.lib.sdl as sdl


logger = get_logger(__name__)


class ANMRenderer(Renderer):
    def __init__(self, window, resource_loader, anm, index=0, sprites=False):
        self.use_fixed_pipeline = window.use_fixed_pipeline #XXX

        Renderer.__init__(self, resource_loader)

        self.window = window
        self.texture_manager.load(resource_loader.instanced_anms.values())

        self._anm = anm
        self.sprites = sprites
        self.clear_color = (0., 0., 0., 1.)
        self.force_allow_dest_offset = False
        self.index_items()
        self.load(index)
        self.objects = [self]

        self.width = 384
        self.height = 448

        self.x = self.width / 2
        self.y = self.height / 2


    def start(self, width=384, height=448):
        self.window.set_size(width, height)

        # Switch to game projection
        proj = perspective(30, float(width) / float(height),
                           101010101./2010101., 101010101./10101.)
        view = setup_camera(0, 0, 1)

        shader = GameShader()

        mvp = view * proj
        shader.bind()
        shader.uniform_matrix('mvp', mvp)


    def load(self, index=None):
        if index is None:
            index = self.num
        self.sprite = Sprite()
        if self.sprites:
            self.sprite.anm = self._anm
            self.sprite.texcoords = self._anm.sprites[index]
            print('Loaded sprite %d' % index)
        else:
            self.anmrunner = ANMRunner(self._anm, index, self.sprite)
            print('Loading anim %d, handled events: %r' % (index, self.anmrunner.script.interrupts.keys()))
        self.num = index


    def change(self, diff):
        keys = self.items.keys()
        keys.sort()
        index = (keys.index(self.num) + diff) % len(keys)
        item = keys[index]
        self.load(item)


    def index_items(self):
        self.items = {}
        if self.sprites:
            self.items = self._anm.sprites
        else:
            self.items = self._anm.scripts


    def toggle_sprites(self):
        self.sprites = not(self.sprites)
        self.index_items()
        self.load(0)


    def toggle_clear_color(self):
        if self.clear_color[0] == 0.:
            self.clear_color = (1., 1., 1., 1.)
        else:
            self.clear_color = (0., 0., 0., 1.)


    def update(self):
        sdl.SCANCODE_C = 6
        sdl.SCANCODE_TAB = 43
        sdl.SCANCODE_SPACE = 44
        sdl.SCANCODE_F1 = 58
        sdl.SCANCODE_F12 = 69
        for event in sdl.poll_events():
            type_ = event[0]
            if type_ == sdl.KEYDOWN:
                scancode = event[1]
                if scancode == sdl.SCANCODE_Z:
                    self.load()
                elif scancode == sdl.SCANCODE_X:
                    self.x, self.y = {(192, 224): (0, 0),
                                      (0, 0): (-224, 0),
                                      (-224, 0): (192, 224)}[(self.x, self.y)]
                elif scancode == sdl.SCANCODE_C:
                    self.force_allow_dest_offset = not self.force_allow_dest_offset
                    self.load()
                elif scancode == sdl.SCANCODE_LEFT:
                    self.change(-1)
                elif scancode == sdl.SCANCODE_RIGHT:
                    self.change(+1)
                elif scancode == sdl.SCANCODE_TAB:
                    self.toggle_sprites()
                elif scancode == sdl.SCANCODE_SPACE:
                    self.toggle_clear_color()
                elif sdl.SCANCODE_F1 <= scancode <= sdl.SCANCODE_F12:
                    interrupt = scancode - sdl.SCANCODE_F1 + 1
                    keys = sdl.get_keyboard_state()
                    if keys[sdl.SCANCODE_LSHIFT]:
                        interrupt += 12
                    if not self.sprites:
                        self.anmrunner.interrupt(interrupt)
                elif scancode == sdl.SCANCODE_ESCAPE:
                    return False
            elif type_ == sdl.QUIT:
                return False
            elif type_ == sdl.WINDOWEVENT:
                event_ = event[1]
                if event_ == sdl.WINDOWEVENT_RESIZED:
                    self.window.set_size(event[2], event[3])

        if not self.sprites:
            self.anmrunner.run_frame()

        if self.force_allow_dest_offset:
            self.sprite.allow_dest_offset = True

        glClearColor(self.clear_color[0], self.clear_color[1], self.clear_color[2], self.clear_color[3])
        glClear(GL_COLOR_BUFFER_BIT)
        if not self.sprite.removed:
            self.render_elements([self])
        return True


    def finish(self):
        pass
