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


from struct import pack, unpack, calcsize
from pytouhou.utils.helpers import read_string, get_logger

logger = get_logger(__name__)


class Model(object):
    def __init__(self):
        self.unknown = 0
        self.bounding_box = (0., 0., 0.,
                             0., 0., 0.)
        self.quads = []



class Stage(object):
    _instructions = {0: ('fff', 'set_viewpos'),
                     1: ('BBBBff', 'set_fog'),
                     2: ('fff', 'set_viewpos2'),
                     3: ('III', 'start_interpolating_viewpos2'),
                     4: ('III', 'start_interpolating_fog')}

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

        stage.name = read_string(file, 128, 'shift_jis')

        bgm_a = read_string(file, 128, 'shift_jis')
        bgm_b = read_string(file, 128, 'shift_jis')
        bgm_c = read_string(file, 128, 'shift_jis')
        bgm_d = read_string(file, 128, 'shift_jis')

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
                script_index, x, y, z, width, height = unpack('<Hxxfffff', file.read(24))
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
            frame, opcode, size = unpack('<IHH', file.read(8))
            if (frame, opcode, size) == (0xffffffff, 0xffff, 0xffff):
                break
            if size != 0x0c:
                raise Exception #TODO
            data = file.read(size)
            if opcode in cls._instructions:
                args = unpack('<%s' % cls._instructions[opcode][0], data)
            else:
                args = (data,)
                logger.warn('unknown opcode %d', opcode)
            stage.script.append((frame, opcode, args))

        return stage


    def write(self, file):
        model_offsets = []
        second_section_offset = 0
        third_section_offset = 0

        nb_faces = sum(len(model.quads) for model in self.models)

        # Write header
        file.write(pack('<HH', len(self.models), nb_faces)) #TODO: nb_faces
        file.write(pack('<II', 0, 0))
        file.write(pack('<I', 0))
        file.write(pack('<128s', self.name.encode('shift_jis')))
        for bgm_name, bgm_path in self.bgms:
            file.write(pack('<128s', bgm_name.encode('shift_jis')))
        for bgm_name, bgm_path in self.bgms:
            file.write(pack('<128s', bgm_path.encode('ascii')))
        file.write(b'\x00\x00\x00\x00' * len(self.models))

        # Write first section
        for i, model in enumerate(self.models):
            model_offsets.append(file.tell())
            file.write(pack('<HHffffff', i, model.unknown, *model.bounding_box))
            for quad in model.quads:
                file.write(pack('<HH', 0x00, 0x1c))
                file.write(pack('<Hxxfffff', *quad))
            file.write(pack('<HH', 0xffff, 4))

        # Write second section
        second_section_offset = file.tell()
        for obj_id, x, y, z in self.object_instances:
            file.write(pack('<HHfff', obj_id, 256, x, y, z))
        file.write(b'\xff' * 16)

        # Write third section
        third_section_offset = file.tell()
        for frame, opcode, args in self.script:
            size = calcsize(self._instructions[opcode][0])
            file.write(pack('<IHH%s' % self._instructions[opcode][0], frame, opcode, size, *args))
        file.write(b'\xff' * 20)

        # Fix offsets
        file.seek(4)
        file.write(pack('<II', second_section_offset, third_section_offset))
        file.seek(16+128+128*2*4)
        file.write(pack('<%sI' % len(self.models), *model_offsets))

