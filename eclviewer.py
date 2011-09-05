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

import pygame

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

    # Renderer
    renderer = GameRenderer(resource_loader, game, background)
    renderer.start()

    # Let's go!
    print(stage.name)

    # Main loop
    clock = pygame.time.Clock()
    while True:
        # Check events
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q)):
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT:
                    pygame.display.toggle_fullscreen()
        keystate = 0 #TODO

        # Update game
        background.update(game.game_state.frame) #TODO
        game.run_iter(keystate)

        # Draw everything
        renderer.render()

        pygame.display.flip()

        clock.tick(120)



try:
    file_path, stage_num = sys.argv[1:]
    stage_num = int(stage_num)
except ValueError:
    print('Usage: %s game_dir_path stage_num' % sys.argv[0])
else:
    main(file_path, stage_num)

