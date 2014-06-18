# -*- encoding: utf-8 -*-
##
## Copyright (C) 2014 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from argparse import ArgumentParser


def parse_arguments(defaults):
    parser = ArgumentParser(description='Libre reimplementation of the Touhou 6 engine.')

    parser.add_argument('data', metavar='DAT', default=defaults['data'], nargs='*', help='Game’s data files')
    parser.add_argument('-p', '--path', metavar='DIRECTORY', default='.', help='Game directory path.')
    parser.add_argument('--debug', action='store_true', help='Set unlimited continues, and perhaps other debug features.')
    parser.add_argument('--verbosity', metavar='VERBOSITY', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Select the wanted logging level.')

    game_group = parser.add_argument_group('Game options')
    game_group.add_argument('-s', '--stage', metavar='STAGE', type=int, default=None, help='Stage, 1 to 7 (Extra), nothing means story mode.')
    game_group.add_argument('-r', '--rank', metavar='RANK', type=int, default=0, help='Rank, from 0 (Easy, default) to 3 (Lunatic).')
    game_group.add_argument('-c', '--character', metavar='CHARACTER', type=int, default=0, help='Select the character to use, from 0 (ReimuA, default) to 3 (MarisaB).')
    game_group.add_argument('-b', '--boss-rush', action='store_true', help='Fight only bosses.')
    game_group.add_argument('--game', metavar='GAME', choices=['EoSD'], default='EoSD', help='Select the game engine to use.')
    game_group.add_argument('--interface', metavar='INTERFACE', choices=['EoSD', 'Sample'], default='EoSD', help='Select the interface to use.')
    game_group.add_argument('--hints', metavar='HINTS', default=None, help='Hints file, to display text while playing.')

    replay_group = parser.add_argument_group('Replay options')
    replay_group.add_argument('--replay', metavar='REPLAY', help='Select a file to replay.')
    replay_group.add_argument('--save-replay', metavar='REPLAY', help='Save the upcoming game into a replay file.')
    replay_group.add_argument('--skip-replay', action='store_true', help='Skip the replay and start to play when it’s finished.')

    netplay_group = parser.add_argument_group('Netplay options')
    netplay_group.add_argument('--port', metavar='PORT', type=int, default=0, help='Local port to use.')
    netplay_group.add_argument('--remote', metavar='REMOTE', default=None, help='Remote address.')
    netplay_group.add_argument('--friendly-fire', action='store_true', help='Allow friendly-fire during netplay.')

    graphics_group = parser.add_argument_group('Graphics options')
    graphics_group.add_argument('--backend', metavar='BACKEND', choices=['opengl', 'sdl'], default=['opengl', 'sdl'], nargs='*', help='Which backend to use (opengl or sdl).')
    graphics_group.add_argument('--fps-limit', metavar='FPS', default=-1, type=int, help='Set fps limit. A value of 0 disables fps limiting, while a negative value limits to 60 fps if and only if vsync doesn’t work.')
    graphics_group.add_argument('--no-background', action='store_false', help='Disable background display (huge performance boost on slow systems).')
    graphics_group.add_argument('--no-particles', action='store_false', help='Disable particles handling (huge performance boost on slow systems).')
    graphics_group.add_argument('--no-sound', action='store_false', help='Disable music and sound effects.')

    opengl_group = parser.add_argument_group('OpenGL backend options')
    opengl_group.add_argument('--gl-flavor', choices=['core', 'es', 'compatibility', 'legacy'], default='compatibility', help='OpenGL profile to use.')
    opengl_group.add_argument('--gl-version', default=2.1, type=float, help='OpenGL version to use.')

    double_buffer = opengl_group.add_mutually_exclusive_group()
    double_buffer.add_argument('--double-buffer', dest='double_buffer', action='store_true', default=None, help='Enable double buffering.')
    double_buffer.add_argument('--single-buffer', dest='double_buffer', action='store_false', default=None, help='Disable double buffering.')

    return parser.parse_args()
