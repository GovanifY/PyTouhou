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

import os
from ConfigParser import RawConfigParser, NoOptionError

from pytouhou.utils.xdg import load_config_paths, save_config_path


class Options(object):
    def __init__(self, name, defaults):
        load_paths = list(reversed([os.path.join(directory, '%s.cfg' % name)
                                    for directory
                                    in load_config_paths(name)]))
        self.save_path = os.path.join(save_config_path(name), '%s.cfg' % name)

        self.config = RawConfigParser(defaults)
        self.paths = self.config.read(load_paths)
        self.section = name if self.config.has_section(name) else 'DEFAULT'

    def get(self, option):
        try:
            return self.config.get(self.section, option)
        except NoOptionError:
            return None

    def set(self, option, value):
        if value is not None:
            self.config.set(self.section, option, value)
        else:
            self.config.remove_option(self.section, option)

        defaults = self.config._defaults
        self.config._defaults = None
        with open(self.save_path, 'w') as save_file:
            self.config.write(save_file)
        self.config._defaults = defaults


def patch_argument_parser():
    from argparse import ArgumentParser, _ActionsContainer

    original_method = _ActionsContainer.add_argument

    def add_argument(self, *args, **kwargs):
        if 'default' not in kwargs:
            dest = kwargs.get('dest')
            if dest is None:
                for dest in args:
                    dest = dest.lstrip('-')
                    value = self.default.get(dest)
                    if value is not None:
                        break
            else:
                dest = dest.replace('_', '-')
                value = self.default.get(dest)
            if value is not None:
                argument_type = kwargs.get('type')
                if argument_type is not None:
                    value = argument_type(value)
                action = kwargs.get('action')
                if action == 'store_true':
                    value = value.lower() == 'true'
                elif action == 'store_false':
                    value = value.lower() != 'true'
                if kwargs.get('nargs') == '*' and isinstance(value, str):
                    value = value.split()
                kwargs['default'] = value
            elif dest == 'double-buffer':
                kwargs['default'] = None
        return original_method(self, *args, **kwargs)
    _ActionsContainer.add_argument = add_argument

    class Parser(ArgumentParser):
        def __init__(self, *args, **kwargs):
            self.default = kwargs.pop('default')
            ArgumentParser.__init__(self, *args, **kwargs)

        def add_argument_group(self, *args, **kwargs):
            group = ArgumentParser.add_argument_group(self, *args, **kwargs)
            group.default = self.default
            group.add_argument_group = self.add_argument_group
            group.add_mutually_exclusive_group = self.add_mutually_exclusive_group
            return group

        def add_mutually_exclusive_group(self, *args, **kwargs):
            group = ArgumentParser.add_mutually_exclusive_group(self, *args, **kwargs)
            group.default = self.default
            group.add_argument_group = self.add_argument_group
            group.add_mutually_exclusive_group = self.add_mutually_exclusive_group
            return group

    return Parser


ArgumentParser = patch_argument_parser()


def parse_config(section, defaults):
    return Options(section, defaults)


def parse_arguments(defaults):
    parser = ArgumentParser(description='Libre reimplementation of the Touhou 6 engine.', default=defaults)

    parser.add_argument('data', metavar='DAT', nargs='*', help='Game’s data files')
    parser.add_argument('-p', '--path', metavar='DIRECTORY', help='Game directory path.')
    parser.add_argument('--debug', action='store_true', help='Set unlimited continues, and perhaps other debug features.')
    parser.add_argument('--verbosity', metavar='VERBOSITY', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Select the wanted logging level.')
    parser.add_argument('--no-menu', action='store_true', help='Disable the menu.')

    game_group = parser.add_argument_group('Game options')
    game_group.add_argument('-s', '--stage', metavar='STAGE', type=int, help='Stage, 1 to 7 (Extra), nothing means story mode.')
    game_group.add_argument('-r', '--rank', metavar='RANK', type=int, help='Rank, from 0 (Easy, default) to 3 (Lunatic).')
    game_group.add_argument('-c', '--character', metavar='CHARACTER', type=int, help='Select the character to use, from 0 (ReimuA, default) to 3 (MarisaB).')
    game_group.add_argument('-b', '--boss-rush', action='store_true', help='Fight only bosses.')
    game_group.add_argument('--game', metavar='GAME', choices=['EoSD'], help='Select the game engine to use.')
    game_group.add_argument('--interface', metavar='INTERFACE', choices=['EoSD', 'Sample'], help='Select the interface to use.')
    game_group.add_argument('--hints', metavar='HINTS', help='Hints file, to display text while playing.')

    replay_group = parser.add_argument_group('Replay options')
    replay_group.add_argument('--replay', metavar='REPLAY', help='Select a file to replay.')
    replay_group.add_argument('--save-replay', metavar='REPLAY', help='Save the upcoming game into a replay file.')
    replay_group.add_argument('--skip-replay', action='store_true', help='Skip the replay and start to play when it’s finished.')

    netplay_group = parser.add_argument_group('Netplay options')
    netplay_group.add_argument('--port', metavar='PORT', type=int, help='Local port to use.')
    netplay_group.add_argument('--remote', metavar='REMOTE', help='Remote address.')
    netplay_group.add_argument('--friendly-fire', action='store_true', help='Allow friendly-fire during netplay.')

    graphics_group = parser.add_argument_group('Graphics options')
    graphics_group.add_argument('--backend', metavar='BACKEND', choices=['opengl', 'sdl'], nargs='*', help='Which backend to use (opengl or sdl).')
    graphics_group.add_argument('--fps-limit', metavar='FPS', type=int, help='Set fps limit. A value of 0 disables fps limiting, while a negative value limits to 60 fps if and only if vsync doesn’t work.')
    graphics_group.add_argument('--frameskip', metavar='FRAMESKIP', type=int, help='Set the frameskip, as 1/FRAMESKIP, or disabled if 0.')
    graphics_group.add_argument('--no-background', action='store_false', help='Disable background display (huge performance boost on slow systems).')
    graphics_group.add_argument('--no-particles', action='store_false', help='Disable particles handling (huge performance boost on slow systems).')
    graphics_group.add_argument('--no-sound', action='store_false', help='Disable music and sound effects.')

    opengl_group = parser.add_argument_group('OpenGL backend options')
    opengl_group.add_argument('--gl-flavor', choices=['core', 'es', 'compatibility', 'legacy'], help='OpenGL profile to use.')
    opengl_group.add_argument('--gl-version', type=float, help='OpenGL version to use.')

    double_buffer = opengl_group.add_mutually_exclusive_group()
    double_buffer.add_argument('--double-buffer', dest='double_buffer', action='store_true', help='Enable double buffering.')
    double_buffer.add_argument('--single-buffer', dest='double_buffer', action='store_false', help='Disable double buffering.')

    return parser.parse_args()
