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

cimport cython

from pytouhou.lib cimport sdl

from .window cimport Window, Runner
from .music import MusicPlayer, SFXPlayer, NullPlayer
from pytouhou.game.game cimport Game


cdef class GameRunner(Runner):
    cdef object background, con, resource_loader, keys, replay_level, common
    cdef Game game
    cdef Window window
    cdef list save_keystates
    cdef bint skip

    # Since we want to support multiple renderers, don’t specify its type.
    #TODO: find a way to still specify its interface.
    cdef object renderer

    def __init__(self, Window window, renderer, common, resource_loader,
                 bint skip=False, con=None):
        self.renderer = renderer
        self.common = common
        self.resource_loader = resource_loader

        self.window = window
        self.replay_level = None
        self.skip = skip
        self.con = con

        self.width = common.interface.width
        self.height = common.interface.height


    def load_game(self, Game game, background=None, bgms=None, replay=None,
                  save_keystates=None):
        self.game = game
        self.background = background

        if self.renderer is not None:
            self.renderer.load_textures(self.resource_loader.instanced_anms)
            self.renderer.load_background(background)

        self.set_input(replay)
        if replay and replay.levels[game.stage - 1]:
            game.players[0].lives = self.replay_level.lives
            game.players[0].power = self.replay_level.power
            game.players[0].bombs = self.replay_level.bombs
            game.difficulty = self.replay_level.difficulty

        self.save_keystates = save_keystates

        null_player = NullPlayer()
        if bgms is not None:
            game.music = MusicPlayer(self.resource_loader, bgms)
            game.music.play(0)
        else:
            game.music = null_player

        game.sfx_player = SFXPlayer(self.resource_loader) if not self.skip else null_player


    cdef void set_input(self, replay=None) except *:
        if not replay or not replay.levels[self.game.stage-1]:
            self.replay_level = None
        else:
            self.replay_level = replay.levels[self.game.stage-1]
            self.keys = self.replay_level.iter_keystates()


    @cython.cdivision(True)
    cdef void set_renderer_size(self, long width, long height) except *:
        if self.renderer is not None:
            runner_width = float(self.width)
            runner_height = float(self.height)

            scale = min(width / runner_width,
                        height / runner_height)

            new_width = <long>(runner_width * scale)
            new_height = <long>(runner_height * scale)

            x = (width - new_width) // 2
            y = (height - new_height) // 2

            self.renderer.size = x, y, new_width, new_height


    cdef void start(self) except *:
        if self.renderer is not None:
            self.set_renderer_size(self.width, self.height)
            self.renderer.start(self.common)


    cdef bint update(self) except *:
        cdef long keystate

        if self.background is not None:
            self.background.update(self.game.frame)
        for event in sdl.poll_events():
            type_ = event[0]
            if type_ == sdl.KEYDOWN:
                scancode = event[1]
                if scancode == sdl.SCANCODE_ESCAPE:
                    return False #TODO: implement the pause.
            elif type_ == sdl.QUIT:
                return False
            elif type_ == sdl.WINDOWEVENT:
                event_ = event[1]
                if event_ == sdl.WINDOWEVENT_RESIZED:
                    self.set_renderer_size(event[2], event[3])
                    if self.window is not None:
                        self.window.set_size(event[2], event[3])
        if self.replay_level is None:
            #TODO: allow user settings
            keys = sdl.get_keyboard_state()
            keystate = 0
            if keys[sdl.SCANCODE_Z]:
                keystate |= 1
            if keys[sdl.SCANCODE_X]:
                keystate |= 2
            if keys[sdl.SCANCODE_LSHIFT]:
                keystate |= 4
            if keys[sdl.SCANCODE_UP]:
                keystate |= 16
            if keys[sdl.SCANCODE_DOWN]:
                keystate |= 32
            if keys[sdl.SCANCODE_LEFT]:
                keystate |= 64
            if keys[sdl.SCANCODE_RIGHT]:
                keystate |= 128
            if keys[sdl.SCANCODE_LCTRL]:
                keystate |= 256
        else:
            try:
                keystate = self.keys.next()
            except StopIteration:
                keystate = 0
                if self.skip:
                    self.set_input()
                    self.skip = False
                    self.game.sfx_player = SFXPlayer(self.resource_loader)

        if self.save_keystates is not None:
            self.save_keystates.append(keystate)

        if self.con is not None:
            self.con.run_iter(self.game, keystate)
        else:
            self.game.run_iter([keystate])

        if self.window is not None:
            self.game.interface.labels['framerate'].set_text('%.2ffps' % self.window.get_fps())
        if not self.skip and self.renderer is not None:
            self.renderer.render(self.game)
        return True
