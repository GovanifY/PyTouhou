# -*- encoding: utf-8 -*-
##
## Copyright (C) 2013 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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


from collections import OrderedDict


def _read_n_int(value):
    values = value.split(', ')
    return tuple(int(value) for value in values)


class Stage(list):
    def __init__(self, number):
        list.__init__(self)
        self.number = number


class Hint:
    _fields = {'Stage': int,
               'Tips': None,
               'Remain': int,
               'Text': lambda v: v[1:-1],
               'Pos': _read_n_int,
               'Count': int,
               'Base': str,
               'Align': str,
               'Time': int,
               'Alpha': int,
               'Color': _read_n_int,
               'Scale': float,
               'End': None,
               'StageEnd': None}


    def __init__(self):
        self.version = 0.0
        self.stages = []


    @classmethod
    def read(cls, file):
        tokens = []

        for line in file:
            line = line.strip()

            if not line:
                continue
            if line[0] == '#':
                continue
            if line == 'Version = 0.0':
                continue

            field, _, value = line.partition(':')
            field = field.rstrip()
            value = value.lstrip()
            parser = cls._fields[field]

            if parser:
                tokens.append((field, parser(value)))
            else:
                tokens.append((field, None))

        stage_mode = False
        tip_mode = False
        stage = None
        tip = None
        hints = cls()
        stages = hints.stages

        for token in tokens:
            key = token[0]
            value = token[1]

            if stage_mode:
                if key != 'StageEnd':
                    if tip_mode:
                        if key != 'End':
                            tip[key] = value
                        else:
                            assert tip_mode == True
                            stage.append(tip)
                            tip_mode = False
                    elif key == 'Tips':
                        assert tip_mode == False
                        tip = OrderedDict()
                        tip_mode = True
                else:
                    assert stage_mode == True
                    stages.append(stage)
                    stage_mode = False
            elif key == 'Stage':
                assert stage_mode == False
                stage = Stage(value)
                stage_mode = True

        return hints


    def write(self, file):
        file.write('# Hints file generated with PyTouhou\n\n\n')

        file.write('Version = {}\n\n'.format(self.version))

        for stage in self.stages:
            file.write('# ================================== \n')
            file.write('Stage : {}\n\n'.format(stage.number))

            for tip in stage:
                file.write('Tips\n')

                for key, value in tip.items():
                    if key == 'Text':
                        value = '"{}"'.format(value)
                    elif key == 'Pos':
                        key = 'Pos\t'
                    if isinstance(value, tuple):
                        value = str(value)[1:-1]
                    file.write('\t{}\t: {}\n'.format(key, value))

                file.write('End\n\n')

            file.write('StageEnd\n')
