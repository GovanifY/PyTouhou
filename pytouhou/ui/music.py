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

from pyglet.media import AudioData, AudioFormat, Player
from pyglet.media.riff import WaveSource


class InfiniteWaveSource(WaveSource):
    def __init__(self, filename, start, end, file=None):
        WaveSource.__init__(self, filename, file)

        self._start = self.audio_format.bytes_per_sample * start
        self._end = self.audio_format.bytes_per_sample * end

        if self._end > self._max_offset:
            raise Exception #TODO

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
            track = resource_loader.get_track(posname)
            wavname = join(resource_loader.game_dir, bgm[1].replace('.mid', '.wav'))
            try:
                source = InfiniteWaveSource(wavname, track.start, track.end)
            except IOError:
                source = None
            self.bgms.append(source)

        self.player = Player()


    def play(self, index):
        bgm = self.bgms[index]
        if self.player.playing:
            self.player.next()
        if bgm:
            self.player.queue(bgm)
        self.player.play()

