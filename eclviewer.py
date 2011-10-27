#!/usr/bin/env python
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

import argparse
import os

import pyximport
pyximport.install()

from pytouhou.resource.loader import Loader
from pytouhou.game.background import Background
from pytouhou.opengl.gamerunner import GameRunner
from pytouhou.game.games import EoSDGame
from pytouhou.game.player import PlayerState
from pytouhou.formats.t6rp import T6RP


def main(path, stage_num, rank, character, replay):
    if replay:
        with open(replay, 'rb') as file:
            replay = T6RP.read(file)
        rank = replay.rank
        character = replay.character
        if not replay.levels[stage_num-1]:
            raise Exception
        from pytouhou.utils.random import Random
        prng = Random(replay.levels[stage_num-1].random_seed)
    else:
        prng = None

    resource_loader = Loader()
    resource_loader.scan_archives(os.path.join(path, name)
                                    for name in ('CM.DAT', 'ST.DAT'))
    game = EoSDGame(resource_loader, [PlayerState(character=character)], stage_num, rank, 16,
                    prng=prng)

    # Load stage data
    stage = resource_loader.get_stage('stage%d.std' % stage_num)

    background_anm_wrapper = resource_loader.get_anm_wrapper(('stg%dbg.anm' % stage_num,))
    background = Background(stage, background_anm_wrapper)

    # Let's go!
    print(stage.name)

    # Main loop
    runner = GameRunner(resource_loader, game, background, replay=replay)
    runner.start()


parser = argparse.ArgumentParser(description='Libre reimplementation of the Touhou 6 engine.')

parser.add_argument('-p', '--path', metavar='DIRECTORY', default='.', help='Game directory path.')
parser.add_argument('-s', '--stage', metavar='STAGE', type=int, required=True, help='Stage, 1 to 7 (Extra).')
parser.add_argument('-r', '--rank', metavar='RANK', type=int, default=0, help='Rank, from 0 (Easy, default) to 3 (Lunatic).')
parser.add_argument('-c', '--character', metavar='CHARACTER', type=int, default=0, help='Select the character to use, from 0 (ReimuA, default) to 3 (MarisaB).')
parser.add_argument('--replay', metavar='REPLAY', help='Select a replay')

args = parser.parse_args()

main(args.path, args.stage, args.rank, args.character, args.replay)
