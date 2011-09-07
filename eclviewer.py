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

import sys
import os

from pytouhou.resource.loader import Loader
from pytouhou.game.background import Background
from pytouhou.opengl.gamerenderer import GameRenderer
from pytouhou.game.game import Game
from pytouhou.game.player import Player


def main(path, stage_num):
    resource_loader = Loader()
    resource_loader.scan_archives(os.path.join(path, name)
                                    for name in ('CM.DAT', 'ST.DAT'))
    game = Game(resource_loader, [Player()], stage_num, 3, 16)

    # Load stage data
    stage = resource_loader.get_stage('stage%d.std' % stage_num)

    background_anm_wrapper = resource_loader.get_anm_wrapper(('stg%dbg.anm' % stage_num,))
    background = Background(stage, background_anm_wrapper)

    # Let's go!
    print(stage.name)

    # Main loop
    renderer = GameRenderer(resource_loader, game, background)
    renderer.start()


try:
    file_path, stage_num = sys.argv[1:]
    stage_num = int(stage_num)
except ValueError:
    print('Usage: %s game_dir_path stage_num' % sys.argv[0])
else:
    main(file_path, stage_num)

