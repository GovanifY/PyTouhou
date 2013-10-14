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

from pytouhou.lib cimport sdl

from .window cimport Window, Runner
from .gamerenderer cimport GameRenderer
from .music import MusicPlayer, SFXPlayer, NullPlayer


cdef class GameRunner(Runner):
    cdef object game, background, con
    cdef GameRenderer renderer
    cdef Window window
    cdef object replay_level, save_keystates
    cdef bint skip

    def __init__(self, Window window, resource_loader, bint skip=False,
                 con=None):
        self.renderer = GameRenderer(resource_loader, window.use_fixed_pipeline)

        self.window = window
        self.replay_level = None
        self.skip = skip
        self.con = con

        self.width = window.width #XXX
        self.height = window.height #XXX


    def load_game(self, game=None, background=None, bgms=None, replay=None, save_keystates=None):
        self.game = game
        self.background = background

        self.renderer.texture_manager.load(game.resource_loader.instanced_anms.values())
        self.renderer.load_background(background)

        self.set_input(replay)
        if replay and replay.levels[game.stage - 1]:
            game.players[0].lives = self.replay_level.lives
            game.players[0].power = self.replay_level.power
            game.players[0].bombs = self.replay_level.bombs
            game.difficulty = self.replay_level.difficulty

        self.save_keystates = save_keystates

        null_player = NullPlayer()
        if bgms:
            game.music = MusicPlayer(game.resource_loader, bgms)
            game.music.play(0)
        else:
            game.music = null_player

        game.sfx_player = SFXPlayer(game.resource_loader) if not self.skip else null_player


    def set_input(self, replay=None):
        if not replay or not replay.levels[self.game.stage-1]:
            self.replay_level = None
        else:
            self.replay_level = replay.levels[self.game.stage-1]
            self.keys = self.replay_level.iter_keystates()


    cdef void start(self) except *:
        cdef long width, height
        width = self.game.interface.width if self.game is not None else 640
        height = self.game.interface.height if self.game is not None else 480
        if width != self.width or height != self.height:
            self.window.set_size(width, height)

        self.renderer.start(self.game)


    cdef bint update(self) except *:
        cdef long keystate

        if self.background:
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
                    self.window.set_size(event[2], event[3])
        if self.game:
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
                        self.game.sfx_player = SFXPlayer(self.game.resource_loader)

            if self.save_keystates is not None:
                self.save_keystates.append(keystate)

            if self.con is not None:
                self.con.run_iter(self.game, keystate)
            else:
                self.game.run_iter([keystate])

            self.game.interface.labels['framerate'].set_text('%.2ffps' % self.window.get_fps())
        if not self.skip:
            self.renderer.render(self.game, self.window)
        return True
