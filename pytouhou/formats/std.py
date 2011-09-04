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


from struct import pack, unpack
from pytouhou.utils.helpers import read_string, get_logger

logger = get_logger(__name__)


class Model(object):
    def __init__(self):
        self.unknown = 0
        self.bounding_box = (0., 0., 0.,
                             0., 0., 0.)
        self.quads = []



class Stage(object):
    def __init__(self):
        self.name = ''
        self.bgms = (('', ''), ('', ''), ('', ''))
        self.models = []
        self.object_instances = []
        self.script = []


    @classmethod
    def read(cls, file):
        stage = Stage()

        nb_models, nb_faces = unpack('<HH', file.read(4))
        object_instances_offset, script_offset = unpack('<II', file.read(8))
        if file.read(4) != b'\x00\x00\x00\x00':
            raise Exception #TODO

        stage.name = read_string(file, 128, 'shift-jis')

        bgm_a = read_string(file, 128, 'shift-jis')
        bgm_b = read_string(file, 128, 'shift-jis')
        bgm_c = read_string(file, 128, 'shift-jis')
        bgm_d = read_string(file, 128, 'shift-jis')

        bgm_a_path = read_string(file, 128, 'ascii')
        bgm_b_path = read_string(file, 128, 'ascii')
        bgm_c_path = read_string(file, 128, 'ascii')
        bgm_d_path = read_string(file, 128, 'ascii')

        stage.bgms = [(bgm_a, bgm_a_path), (bgm_b, bgm_b_path), (bgm_c, bgm_c_path), (bgm_d, bgm_d_path)] #TODO: handle ' '

        # Read model definitions
        offsets = unpack('<%s' % ('I' * nb_models), file.read(4 * nb_models))
        for offset in offsets:
            model = Model()
            id_, unknown, x, y, z, width, height, depth = unpack('<HHffffff', file.read(28))
            model.unknown = unknown
            model.bounding_box = x, y, z, width, height, depth #TODO: check
            while True:
                unknown, size = unpack('<HH', file.read(4))
                if unknown == 0xffff:
                    break
                if size != 0x1c:
                    raise Exception #TODO
                script_index, _padding, x, y, z, width, height = unpack('<HHfffff', file.read(24))
                #TODO: store script_index, x, y, z, width and height
                model.quads.append((script_index, x, y, z, width, height))
            stage.models.append(model)


        # Read object usages
        file.seek(object_instances_offset)
        while True:
            obj_id, unknown, x, y, z = unpack('<HHfff', file.read(16))
            if (obj_id, unknown) == (0xffff, 0xffff):
                break
            if unknown != 256:
                raise Exception #TODO
            stage.object_instances.append((obj_id, x, y, z))


        # Read other funny things (script)
        file.seek(script_offset)
        while True:
            frame, message_type, size = unpack('<IHH', file.read(8))
            if (frame, message_type, size) == (0xffffffff, 0xffff, 0xffff):
                break
            if size != 0x0c:
                raise Exception #TODO
            data = file.read(12)
            #TODO: maybe add a name somewhere
            if message_type == 0: # ViewPos
                args = unpack('<fff', data)
            elif message_type == 1: # Color
                args = unpack('<BBBBff', data)
            elif message_type == 2: # ViewPos2
                args = unpack('<fff', data)
            elif message_type == 3:  # StartInterpolatingViewPos2
                args = tuple(unpack('<III', data)[:1])
            elif message_type == 4: # StartInterpolatingFog
                args = tuple(unpack('<III', data)[:1])
            else:
                args = (data,)
                logger.warn('unknown opcode %d (data: %r)', message_type, data)
            stage.script.append((frame, message_type, args))

        return stage

