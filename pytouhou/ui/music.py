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

from pyglet.media import AudioData, AudioFormat, StaticSource, Player
from pyglet.media.riff import WaveSource


from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)


class InfiniteWaveSource(WaveSource):
    def __init__(self, filename, start, end, file=None):
        WaveSource.__init__(self, filename, file)

        self._start = self.audio_format.bytes_per_sample * start
        self._end = self.audio_format.bytes_per_sample * end

        if self._end > self._max_offset:
            raise Exception('Music ends after the end of the file.')

        self._duration = None


    def _get_audio_data(self, bytes):
        bytes -= bytes % self.audio_format.bytes_per_sample

        data = b''
        length = bytes
        while True:
            size = min(length, self._end - self._offset)
            data += self._file.read(size)
            if size == length:
                break

            self._offset = self._start
            self._file.seek(self._offset + self._start_offset)
            length -= size

        self._offset += length

        timestamp = float(self._offset) / self.audio_format.bytes_per_second
        duration = float(bytes) / self.audio_format.bytes_per_second

        return AudioData(data, bytes, timestamp, duration)


    def seek(self, timestamp):
        raise NotImplementedError('irrelevant')


class ZwavSource(InfiniteWaveSource):
    def __init__(self, filename, format, file=None):
        if file is None:
            file = open(filename, 'rb')

        self._file = file

        assert b'ZWAV' == self._file.read(4)

        self.audio_format = AudioFormat(
            channels=format.wChannels,
            sample_size=format.wBitsPerSample,
            sample_rate=format.dwSamplesPerSec)

        self._start_offset = 0
        self._offset = format.intro

        self._file.seek(self._offset)
        self._start = format.intro + format.start
        self._end = format.intro + format.duration


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
                logger.warn('Music description not found: %s', posname)
                continue
            wavname = join(resource_loader.game_dir, bgm[1].replace('.mid', '.wav'))
            try:
                source = InfiniteWaveSource(wavname, track.start, track.end)
            except IOError:
                source = None
            self.bgms.append(source)

        self.player = Player()


    def pause(self):
        self.player.pause()


    def play(self, index):
        bgm = self.bgms[index]
        if self.player.playing:
            self.player.next()
        if bgm:
            self.player.queue(bgm)
        self.player.play()


class SFXPlayer(object):
    def __init__(self, loader, volume=.42):
        self.loader = loader
        self.players = {}
        self.sounds = {}
        self.volume = volume


    def get_player(self, name):
        if name not in self.players:
            self.players[name] = Player()
            self.players[name].volume = self.volume
        return self.players[name]


    def get_sound(self, name):
        if name not in self.sounds:
            wave_file = self.loader.get_file(name)
            self.sounds[name] = StaticSource(WaveSource(name, wave_file))
        return self.sounds[name]


    def play(self, name, volume=None):
        sound = self.get_sound(name)
        player = self.get_player(name)
        if volume:
            player.volume = volume
        if player.playing:
            player.next()
        if sound:
            player.queue(sound)
        player.play()


class NullPlayer(object):
    def __init__(self, loader=None, bgms=None):
        pass


    def play(self, name):
        pass
