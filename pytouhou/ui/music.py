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


from pyglet.media import AudioData
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
