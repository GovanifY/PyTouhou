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


from os.path import join
from glob import glob
from pytouhou.lib import sdl
from pytouhou.lib.sdl cimport load_music, Music, load_chunk, Chunk
from pytouhou.utils.helpers import get_logger
from pytouhou.game.music cimport MusicPlayer

logger = get_logger(__name__)


cdef class BGMPlayer(MusicPlayer):
    cdef list bgms

    def __init__(self, resource_loader, bgms):
        self.bgms = []
        for bgm in bgms:
            if not bgm:
                self.bgms.append(None)
                continue
            posname = bgm[1].replace('bgm/', '').replace('.mid', '.pos')
            try:
                track = resource_loader.get_track(posname)
            except KeyError:
                track = None
                logger.warn('Music description “%s” not found, continuing without looping data.', posname)
            globname = join(resource_loader.game_dir, bgm[1]).replace('.mid', '.*')
            filenames = glob(globname)
            for filename in reversed(filenames):
                try:
                    source = load_music(filename)
                except sdl.SDLError as error:
                    logger.debug('Music file “%s” unreadable: %s', filename, error)
                    continue
                else:
                    if track is not None:
                        source.set_loop_points(track.start / 44100., track.end / 44100.) #TODO: retrieve the sample rate from the actual track.
                    self.bgms.append(source)
                    logger.debug('Music file “%s” opened.', filename)
                    break
            else:
                self.bgms.append(None)
                logger.warn('No working music file for “%s”, disabling bgm.', globname)

    cpdef play(self, index):
        cdef Music bgm
        bgm = self.bgms[index]
        if bgm is not None:
            bgm.play(-1)


cdef class SFXPlayer(MusicPlayer):
    cdef object loader
    cdef dict channels, sounds
    cdef float volume
    cdef int next_channel

    def __init__(self, loader, volume=.42):
        self.loader = loader
        self.channels = {}
        self.sounds = {}
        self.volume = volume
        self.next_channel = 0

    cdef int get_channel(self, name) except -1:
        if name not in self.channels:
            self.channels[name] = self.next_channel
            self.next_channel += 1
        return self.channels[name]

    cdef Chunk get_sound(self, name):
        cdef Chunk chunk
        if name not in self.sounds:
            try:
                wave_file = self.loader.get_file(name)
                chunk = load_chunk(wave_file)
            except (KeyError, sdl.SDLError) as error:
                logger.warn('Sound “%s” not found: %s', name, error)
                chunk = None
            else:
                chunk.set_volume(self.volume)
            self.sounds[name] = chunk
        return self.sounds[name]

    cpdef play(self, name):
        sound = self.get_sound(name)
        if sound is None:
            return
        channel = self.get_channel(name)
        sound.play(channel, 0)

    cpdef set_volume(self, name, float volume):
        sound = self.get_sound(name)
        if sound is not None:
            sound.set_volume(volume)
