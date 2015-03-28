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

"""Stage Definition (STD) files handling.

This module provides classes for handling the Stage Definition file format.
The STD file format is a format used in Touhou 6: EoSD to describe non-gameplay
aspects of a stage: its name, its music, 3D models composing its background,
and various scripted events such as camera movement.
"""


from struct import pack, unpack, calcsize
from pytouhou.utils.helpers import read_string, get_logger

logger = get_logger(__name__)


class Model:
    def __init__(self, unknown=0, bounding_box=None, quads=None):
        self.unknown = 0
        self.bounding_box = bounding_box or (0., 0., 0.,
                                             0., 0., 0.)
        self.quads = quads or []



class Stage:
    """Handle Touhou 6 Stage Definition files.

    Stage Definition files are structured files describing non-gameplay aspects
    aspects of a stage. They are split in a header an 3 additional sections.

    The header contains the name of the stage, the background musics (BGM) used,
    as well as the number of quads and objects composing the background.
    The first section describes the models composing the background, whereas
    the second section dictates how they are used.
    The last section describes the changes to the camera, fog, and other things.

    Instance variables:
    name -- name of the stage
    bgms -- list of (name, path) describing the different background musics used
    models -- list of Model objects
    object_instances -- list of instances of the aforementioned models
    script -- stage script (camera, fog, etc.)
    """

    _instructions = {0: ('fff', 'set_viewpos'),
                     1: ('BBBxff', 'set_fog'),
                     2: ('fff', 'set_viewpos2'),
                     3: ('Ixxxxxxxx', 'start_interpolating_viewpos2'),
                     4: ('Ixxxxxxxx', 'start_interpolating_fog')}

    def __init__(self):
        self.name = ''
        self.bgms = (('', ''), ('', ''), ('', ''), ('', ''))
        self.models = []
        self.object_instances = []
        self.script = []


    @classmethod
    def read(cls, file):
        """Read a Stage Definition file.

        Raise an exception if the file is invalid.
        Return a STD instance otherwise.
        """

        stage = Stage()

        nb_models, nb_faces = unpack('<HH', file.read(4))
        object_instances_offset, script_offset, zero = unpack('<III', file.read(12))
        assert zero == 0

        stage.name = read_string(file, 128, 'shift_jis')

        bgm_a = read_string(file, 128, 'shift_jis')
        bgm_b = read_string(file, 128, 'shift_jis')
        bgm_c = read_string(file, 128, 'shift_jis')
        bgm_d = read_string(file, 128, 'shift_jis')

        bgm_a_path = read_string(file, 128, 'ascii')
        bgm_b_path = read_string(file, 128, 'ascii')
        bgm_c_path = read_string(file, 128, 'ascii')
        bgm_d_path = read_string(file, 128, 'ascii')

        stage.bgms = [None if bgm[0] == u' ' else bgm
            for bgm in ((bgm_a, bgm_a_path), (bgm_b, bgm_b_path), (bgm_c, bgm_c_path), (bgm_d, bgm_d_path))]

        # Read model definitions
        offsets = unpack('<%s' % ('I' * nb_models), file.read(4 * nb_models))
        for offset in offsets:
            model = Model()
            file.seek(offset)

            # Read model header
            id_, unknown, x, y, z, width, height, depth = unpack('<HHffffff', file.read(28))
            model.unknown = unknown
            model.bounding_box = x, y, z, width, height, depth #TODO: check

            # Read model quads
            while True:
                unknown, size = unpack('<HH', file.read(4))
                if unknown == 0xffff:
                    break
                assert size == 0x1c
                script_index, x, y, z, width, height = unpack('<Hxxfffff', file.read(24))
                model.quads.append((script_index, x, y, z, width, height))
            stage.models.append(model)


        # Read object usages
        file.seek(object_instances_offset)
        while True:
            obj_id, unknown, x, y, z = unpack('<HHfff', file.read(16))
            if (obj_id, unknown) == (0xffff, 0xffff):
                break
            assert unknown == 256 #TODO: really?
            stage.object_instances.append((obj_id, x, y, z))


        # Read the script
        file.seek(script_offset)
        while True:
            frame, opcode, size = unpack('<IHH', file.read(8))
            if (frame, opcode, size) == (0xffffffff, 0xffff, 0xffff):
                break
            assert size == 0x0c
            data = file.read(size)
            if opcode in cls._instructions:
                args = unpack('<%s' % cls._instructions[opcode][0], data)
            else:
                args = (data,)
                logger.warn('unknown opcode %d', opcode)
            stage.script.append((frame, opcode, args))

        return stage


    def write(self, file):
        """Write to a Stage Definition file."""
        model_offsets = []
        second_section_offset = 0
        third_section_offset = 0

        nb_faces = sum(len(model.quads) for model in self.models)

        # Write header (offsets, number of quads, name and background musics)
        file.write(pack('<HH', len(self.models), nb_faces))
        file.write(pack('<II', 0, 0))
        file.write(pack('<I', 0))
        file.write(pack('<128s', self.name.encode('shift_jis')))
        for bgm_name, bgm_path in self.bgms:
            file.write(pack('<128s', bgm_name.encode('shift_jis')))
        for bgm_name, bgm_path in self.bgms:
            file.write(pack('<128s', bgm_path.encode('ascii')))
        file.write(b'\x00\x00\x00\x00' * len(self.models))

        # Write first section (models)
        for i, model in enumerate(self.models):
            model_offsets.append(file.tell())
            file.write(pack('<HHffffff', i, model.unknown, *model.bounding_box))
            for quad in model.quads:
                file.write(pack('<HH', 0x00, 0x1c))
                file.write(pack('<Hxxfffff', *quad))
            file.write(pack('<HH', 0xffff, 4))

        # Write second section (object instances)
        second_section_offset = file.tell()
        for obj_id, x, y, z in self.object_instances:
            file.write(pack('<HHfff', obj_id, 256, x, y, z))
        file.write(b'\xff' * 16)

        # Write third section (script)
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

