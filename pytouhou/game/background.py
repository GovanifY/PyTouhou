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


from pytouhou.utils.interpolator import Interpolator
from pytouhou.vm import ANMRunner
from pytouhou.game.sprite import Sprite


class Background:
    def __init__(self, stage, anm):
        self.stage = stage
        self.anm = anm
        self.last_frame = -1

        self.models = []
        self.object_instances = []
        self.anm_runners = []

        self.position_interpolator = Interpolator((0, 0, 0))
        self.fog_interpolator = Interpolator((0, 0, 0, 0, 0))
        self.position2_interpolator = Interpolator((0, 0, 0))

        self.build_models()
        self.build_object_instances()


    def build_object_instances(self):
        self.object_instances = []
        for model_id, ox, oy, oz in self.stage.object_instances:
            self.object_instances.append((ox, oy, oz, model_id, self.models[model_id]))
        # Z-sorting:
        # TODO z-sorting may be needed at each iteration
        def keyfunc(obj):
            return obj[2] + self.stage.models[obj[3]].bounding_box[2]
        self.object_instances.sort(key=keyfunc, reverse=True)


    def build_models(self):
        self.models = []
        for obj in self.stage.models:
            quads = []
            for script_index, ox, oy, oz, width_override, height_override in obj.quads:
                sprite = Sprite(width_override, height_override)
                anm_runner = ANMRunner(self.anm, script_index, sprite)
                quads.append((ox, oy, oz, width_override, height_override, sprite))
                self.anm_runners.append(anm_runner)
            self.models.append(quads)


    def update(self, frame):
        for frame_num, message_type, args in self.stage.script:
            if self.last_frame < frame_num <= frame:
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

        for i in range(frame - self.last_frame):
            for anm_runner in tuple(self.anm_runners):
                if not anm_runner.run_frame():
                    self.anm_runners.remove(anm_runner)

        self.position2_interpolator.update(frame)
        self.fog_interpolator.update(frame)
        self.position_interpolator.update(frame)

        self.last_frame = frame

