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


from struct import unpack


class Track:
    def __init__(self):
        self.name = ''

        # loop info
        self.intro = 0
        #self.unknown
        self.start = 0
        self.duration = 0

        # WAVE header
        self.wFormatTag = 1
        self.wChannels = 2
        self.dwSamplesPerSec = 44100
        self.dwAvgBytesPerSec = 176400
        self.wBlockAlign = 4
        self.wBitsPerSample = 16


class FMT(list):
    @classmethod
    def read(cls, file):
        self = cls()

        file.seek(0)
        while True:
            track = Track()
            track.name = unpack('<16s', file.read(16))[0]
            if not ord(track.name[0]):
                break

            # loop info
            track.intro, unknown, track.start, track.duration = unpack('<IIII', file.read(16))

            # WAVE header
            (track.wFormatTag,
             track.wChannels,
             track.dwSamplesPerSec,
             track.dwAvgBytesPerSec,
             track.wBlockAlign,
             track.wBitsPerSample) = unpack('<HHLLHH', file.read(16))

            assert track.wFormatTag == 1 # We don’t support non-PCM formats
            assert track.dwAvgBytesPerSec == track.dwSamplesPerSec * track.wBlockAlign
            assert track.wBlockAlign == track.wChannels * track.wBitsPerSample // 8
            zero = file.read(4)
            assert b'\00\00\00\00' == zero

            self.append(track)

        return self

