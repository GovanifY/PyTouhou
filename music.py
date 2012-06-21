#!/usr/bin/env python
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

import argparse
import os

import pyximport
pyximport.install()

from pytouhou.resource.loader import Loader
from pytouhou.ui.music import InfiniteWaveSource, ZwavSource
from pyglet.app import run


def get_wav_source(bgm, resource_loader):
    posname = bgm.replace('bgm/', '').replace('.mid', '.pos')
    track = resource_loader.get_track(posname)
    wavname = os.path.join(resource_loader.game_dir, bgm.replace('.mid', '.wav'))
    try:
        source = InfiniteWaveSource(wavname, track.start, track.end)
    except IOError:
        source = None
    return source


def get_zwav_source(track, resource_loader):
    fmt = resource_loader.get_fmt('thbgm.fmt')
    try:
        source = ZwavSource('thbgm.dat', fmt[track])
    except IOError:
        source = None
    return source


def main(path, track, zwav, data):
    resource_loader = Loader(path)
    resource_loader.scan_archives(data)

    if not zwav:
        source = get_wav_source('bgm/th06_%02d.mid' % track, resource_loader)
    else:
        source = get_zwav_source(track, resource_loader)

    source.play()

    run()


pathsep = os.path.pathsep
default_data = (pathsep.join(('MD.DAT', 'th6*MD.DAT', '*MD.DAT', '*md.dat')),)


parser = argparse.ArgumentParser(description='Player for Touhou 6 music.')

parser.add_argument('data', metavar='DAT', default=default_data, nargs='*', help='Game’s data files')
parser.add_argument('-p', '--path', metavar='DIRECTORY', default='.', help='Game directory path.')
parser.add_argument('-t', '--track', metavar='TRACK', type=int, required=True, help='The track to play, in game order.')
parser.add_argument('-z', '--zwav', action='store_true', default=False, help='Must be set when playing from PCB or newer.')

args = parser.parse_args()

main(args.path, args.track, args.zwav, tuple(args.data))
