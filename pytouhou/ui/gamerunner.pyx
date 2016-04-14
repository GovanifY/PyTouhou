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

from pytouhou.lib.gui cimport EXIT, PAUSE, SCREENSHOT, RESIZE, FULLSCREEN

from .window cimport Window, Runner
from .music import BGMPlayer, SFXPlayer
from pytouhou.game.game cimport Game
from pytouhou.game.music cimport MusicPlayer


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

        null_player = MusicPlayer()
        if bgms is not None:
            game.music = BGMPlayer(self.resource_loader, bgms)
            game.music.play(0)
        else:
            game.music = null_player

        game.sfx_player = SFXPlayer(self.resource_loader) if not self.skip else null_player


    cdef bint set_input(self, replay=None) except True:
        if not replay or not replay.levels[self.game.stage-1]:
            self.replay_level = None
        else:
            self.replay_level = replay.levels[self.game.stage-1]
            self.keys = self.replay_level.iter_keystates()


    @cython.cdivision(True)
    cdef bint set_renderer_size(self, long width, long height) except True:
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


    cdef bint start(self) except True:
        if self.renderer is not None:
            self.set_renderer_size(self.width, self.height)
            self.renderer.start(self.common)


    cdef bint capture(self) except True:
        if self.renderer is not None:
            filename = 'screenshot/frame%06d.ppm' % self.game.frame
            self.renderer.capture(filename, self.width, self.height)


    cpdef bint update(self, bint render) except -1:
        cdef long keystate
        capture = False

        if self.background is not None:
            self.background.update(self.game.frame)
        for event, args in self.window.get_events():
            if event == EXIT:
                return False
            elif event == PAUSE:
                return False  # TODO: implement the pause.
            elif event == FULLSCREEN:
                self.window.toggle_fullscreen()
            elif event == SCREENSHOT:
                capture = True
            elif event == RESIZE:
                width, height = args
                self.set_renderer_size(width, height)
                if self.window is not None:
                    self.window.set_size(width, height)
        if self.replay_level is None:
            keystate = self.window.get_keystate()
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

        labels = self.game.interface.labels
        if self.window is not None and 'framerate' in labels:
            labels['framerate'].set_text('%.2ffps' % self.window.get_fps())

        if render and not self.skip and self.renderer is not None:
            self.renderer.render(self.game)

        if capture:
            self.capture()

        return True
