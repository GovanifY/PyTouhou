from io import BytesIO
import os
import struct
from itertools import chain

from pytouhou.utils.matrix import Matrix
from pytouhou.utils.interpolator import Interpolator

from pytouhou.formats.std import Stage
from pytouhou.formats.anm0 import Animations



class Background(object):
    def __init__(self, archive, stage_num):
        self.stage = Stage.read(BytesIO(archive.extract('stage%d.std' % stage_num)))
        self.anim = Animations.read(BytesIO(archive.extract('stg%dbg.anm' % stage_num)))
        texture_components = [None, None]
        for i, component_name in ((0, self.anim.first_name), (1, self.anim.secondary_name)):
            if component_name:
                texture_components[i] = BytesIO(archive.extract(os.path.basename(component_name)))
        self.texture_components = texture_components
        self.objects = []
        self.object_instances = []
        self._uvs = b''
        self._vertices = b''
        self.build_objects()
        self.build_object_instances()


    def build_object_instances(self):
        self.object_instances = []
        for obj, ox, oy, oz in self.stage.object_instances:
            obj_id = self.stage.objects.index(obj)

            obj_instance = []
            for face_vertices, face_uvs in self.objects[obj_id]:
                obj_instance.append((tuple((x + ox, y + oy, z + oz)
                                        for x, y, z in face_vertices),
                                    face_uvs))
            self.object_instances.append(obj_instance)
        # Z-sorting
        def keyfunc(obj):
            return min(z for face in obj for x, y, z in face[0])
        self.object_instances.sort(key=keyfunc, reverse=True)


    def object_instances_to_vertices_uvs(self):
        vertices = tuple(vertex for obj in self.object_instances
                            for face in obj for vertex in face[0])
        uvs = tuple(uv for obj in self.object_instances
                            for face in obj for uv in face[1])
        return vertices, uvs


    def build_objects(self):
        self.objects = []
        for i, obj in enumerate(self.stage.objects):
            faces = []
            for script_index, x, y, z, width_override, height_override in obj.quads:
                #TODO: refactor
                vertices = []
                uvs = []
                vertmat = Matrix()
                vertmat.data[0][0] = -.5
                vertmat.data[1][0] = -.5

                vertmat.data[0][1] = .5
                vertmat.data[1][1] = -.5

                vertmat.data[0][2] = .5
                vertmat.data[1][2] = .5

                vertmat.data[0][3] = -.5
                vertmat.data[1][3] = .5

                for i in range(4):
                    vertmat.data[2][i] = 0.
                    vertmat.data[3][i] = 1.

                properties = {}
                for time, instr_type, data in self.anim.scripts[script_index]:
                    if instr_type == 15:
                        properties[15] = b''
                        break
                    elif time == 0: #TODO
                        properties[instr_type] = data
                #if 15 not in properties: #TODO: Skip properties
                #    continue

                #TODO: properties 3 and 4
                if 1 in properties:
                    tx, ty, tw, th = self.anim.sprites[struct.unpack('<I', properties[1])[0]]
                width, height = 1., 1.
                if 2 in properties:
                    width, height = struct.unpack('<ff', properties[2])
                width = width_override or width * tw
                height = height_override or height * th
                transform = Matrix.get_scaling_matrix(width, height, 1.)
                if 7 in properties:
                    transform = Matrix.get_scaling_matrix(-1., 1., 1.).mult(transform)
                if 9 in properties:
                    rx, ry, rz = struct.unpack('<fff', properties[9])
                    transform = Matrix.get_rotation_matrix(-rx, 'x').mult(transform)
                    transform = Matrix.get_rotation_matrix(ry, 'y').mult(transform)
                    transform = Matrix.get_rotation_matrix(-rz, 'z').mult(transform) #TODO: minus, really?
                if 23 in properties: # Reposition
                    transform = Matrix.get_translation_matrix(width / 2., height / 2., 0.).mult(transform)
                vertmat = transform.mult(vertmat)

                uvs = [(tx / self.anim.size[0],         1. - (ty / self.anim.size[1])),
                       ((tx + tw) / self.anim.size[0],  1. - (ty / self.anim.size[1])),
                       ((tx + tw) / self.anim.size[0],  1. - ((ty + th) / self.anim.size[1])),
                       (tx / self.anim.size[0],         1. - ((ty + th) / self.anim.size[1]))]

                for i in xrange(4):
                    w = vertmat.data[3][i]
                    vertices.append((vertmat.data[0][i] / w + x,
                                     vertmat.data[1][i] / w + y,
                                     vertmat.data[2][i] / w + z))
                faces.append((vertices, uvs))
            self.objects.append(faces)


    def update(self, frame):
        if not self._uvs or not self._vertices:
            vertices, uvs = self.object_instances_to_vertices_uvs()
            self.nb_vertices = len(vertices)
            vertices_format = 'f' * (3 * self.nb_vertices)
            uvs_format = 'f' * (2 * self.nb_vertices)
            self._vertices = struct.pack(vertices_format, *chain(*vertices))
            self._uvs = struct.pack(uvs_format, *chain(*uvs))

            self.position_interpolator = Interpolator((0, 0, 0))
            self.fog_interpolator = Interpolator((0, 0, 0, 0, 0))
            self.position2_interpolator = Interpolator((0, 0, 0))

        for frame_num, message_type, args in self.stage.script:
            if frame_num == frame:
                if message_type == 1:
                    self.fog_interpolator.set_interpolation_end_values(args)
                elif message_type == 3:
                    duration, = args
                    self.position2_interpolator.set_interpolation_end_frame(frame_num + duration)
                elif message_type == 4:
                    duration, = args
                    self.fog_interpolator.set_interpolation_end_frame(frame_num + duration)
                elif message_type == 2:
                    self.position2_interpolator.set_interpolation_end_values(args)
            if frame_num <= frame and message_type == 0:
                self.position_interpolator.set_interpolation_start(frame_num, args)
            if frame_num > frame and message_type == 0:
                self.position_interpolator.set_interpolation_end(frame_num, args)
                break

        self.position2_interpolator.update(frame)
        self.fog_interpolator.update(frame)
        self.position_interpolator.update(frame)

