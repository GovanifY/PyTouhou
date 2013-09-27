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
from pytouhou.lib cimport sdl
from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)


class MusicPlayer(object):
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
                self.bgms.append(None)
                logger.warn(u'Music description “%s” not found.', posname)
                continue
            globname = join(resource_loader.game_dir, bgm[1].encode('ascii')).replace('.mid', '.*')
            filenames = glob(globname)
            for filename in reversed(filenames):
                try:
                    source = sdl.load_music(filename)
                except sdl.SDLError as error:
                    logger.debug(u'Music file “%s” unreadable: %s', filename, error)
                    continue
                else:
                    source.set_loop_points(track.start / 44100., track.end / 44100.) #TODO: retrieve the sample rate from the actual track.
                    self.bgms.append(source)
                    logger.debug(u'Music file “%s” opened.', filename)
                    break
            else:
                self.bgms.append(None)
                logger.warn(u'No working music file for “%s”, disabling bgm.', globname)

    def play(self, index):
        cdef sdl.Music bgm
        bgm = self.bgms[index]
        if bgm:
            bgm.play(-1)


class SFXPlayer(object):
    def __init__(self, loader, volume=.42):
        self.loader = loader
        self.channels = {}
        self.sounds = {}
        self.volume = volume
        self.next_channel = 0

    def get_channel(self, name):
        if name not in self.channels:
            self.channels[name] = self.next_channel
            self.next_channel += 1
        return self.channels[name]

    def get_sound(self, name):
        if name not in self.sounds:
            wave_file = self.loader.get_file(name)
            chunk = sdl.load_chunk(wave_file)
            chunk.set_volume(self.volume)
            self.sounds[name] = chunk
        return self.sounds[name]

    def play(self, name, volume=None):
        cdef sdl.Chunk sound
        sound = self.get_sound(name)
        channel = self.get_channel(name)
        if volume:
            sdl.mix_volume(channel, volume)
        sound.play(channel, 0)


class NullPlayer(object):
    def __init__(self, loader=None, bgms=None):
        pass

    def play(self, name, volume=None):
        pass
