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


from io import BytesIO
import os
import struct
from itertools import chain

from pytouhou.utils.interpolator import Interpolator
from pytouhou.game.sprite import Sprite


class Background(object):
    def __init__(self, stage, anm_wrapper):
        self.stage = stage
        self.anm_wrapper = anm_wrapper
        self.objects = []
        self.object_instances = []
        self.objects_by_texture = {}

        self.position_interpolator = Interpolator((0, 0, 0))
        self.fog_interpolator = Interpolator((0, 0, 0, 0, 0))
        self.position2_interpolator = Interpolator((0, 0, 0))

        self.build_objects()
        self.build_object_instances()


    def build_object_instances(self):
        self.object_instances = []
        for obj, ox, oy, oz in self.stage.object_instances:
            obj_id = self.stage.objects.index(obj)

            obj_instance = []
            for face_vertices, face_uvs, face_colors in self.objects[obj_id]:
                obj_instance.append((tuple((x + ox, y + oy, z + oz)
                                        for x, y, z in face_vertices),
                                    face_uvs,
                                    face_colors))
            self.object_instances.append(obj_instance)
        # Z-sorting
        def keyfunc(obj):
            return min(z for face in obj for x, y, z in face[0])
        self.object_instances.sort(key=keyfunc, reverse=True)


    def object_instances_to_vertices_uvs_colors(self):
        vertices = tuple(vertex for obj in self.object_instances
                            for face in obj for vertex in face[0])
        uvs = tuple(uv for obj in self.object_instances
                            for face in obj for uv in face[1])
        colors = tuple(color for obj in self.object_instances
                            for face in obj for color in face[2])
        return vertices, uvs, colors


    def build_objects(self):
        self.objects = []
        for i, obj in enumerate(self.stage.objects):
            faces = []
            for script_index, ox, oy, oz, width_override, height_override in obj.quads:
                #TODO: per-texture rendering
                anm, sprite = self.anm_wrapper.get_sprite(script_index)
                if sprite.update():
                    sprite.update_vertices_uvs_colors(width_override, height_override)
                uvs, vertices = sprite._uvs, tuple((x + ox, y + oy, z + oz) for x, y, z in sprite._vertices)
                colors = sprite._colors
                faces.append((vertices, uvs, colors))
            self.objects.append(faces)


    def update(self, frame):
        if not self.objects_by_texture:
            vertices, uvs, colors = self.object_instances_to_vertices_uvs_colors()
            nb_vertices = len(vertices)
            vertices_format = 'f' * (3 * nb_vertices)
            uvs_format = 'f' * (2 * nb_vertices)
            colors_format = 'B' * (4 * nb_vertices)
            vertices = struct.pack(vertices_format, *chain(*vertices))
            uvs = struct.pack(uvs_format, *chain(*uvs))
            colors = struct.pack(colors_format, *chain(*colors))
            assert len(self.anm_wrapper.anm_files) == 1 #TODO
            anm = self.anm_wrapper.anm_files[0]
            self.objects_by_texture = {(anm.first_name, anm.secondary_name): (nb_vertices, vertices, uvs, colors)}

        for frame_num, message_type, args in self.stage.script:
            if frame_num == frame:
                if message_type == 0:
                    self.position_interpolator.set_interpolation_start(frame_num, args)
                elif message_type == 1:
                    self.fog_interpolator.set_interpolation_end_values(args)
                elif message_type == 2:
                    self.position2_interpolator.set_interpolation_end_values(args)
                elif message_type == 3:
                    duration, = args
                    self.position2_interpolator.set_interpolation_end_frame(frame_num + duration)
                elif message_type == 4:
                    duration, = args
                    self.fog_interpolator.set_interpolation_end_frame(frame_num + duration)
            if frame_num > frame and message_type == 0:
                self.position_interpolator.set_interpolation_end(frame_num, args)
                break

        self.position2_interpolator.update(frame)
        self.fog_interpolator.update(frame)
        self.position_interpolator.update(frame)

