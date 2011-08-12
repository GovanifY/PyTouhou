from struct import unpack

from pytouhou.utils.matrix import Matrix


class AnmWrapper(object):
    def __init__(self, anm_files):
        self.anm_files = list(anm_files)

    def get_sprite(self, script_index):
        for anm in self.anm_files:
            if script_index in anm.scripts:
                return anm, Sprite(anm, script_index)



class Sprite(object):
    def __init__(self, anm, script_index):
        self.anm = anm
        self.script_index = script_index
        self.texcoords = (0, 0, 0, 0) # x, y, width, height
        self.mirrored = False
        self.rescale = (1., 1.)
        self.rotations_3d = (0., 0., 0.)
        self.rotations_speed_3d = (0., 0., 0.)
        self.corner_relative_placement = False
        self.frame = 0
        self._uvs = []
        self._vertices = []


    def update_uvs_vertices(self, override_width=0, override_height=0):
        vertmat = Matrix([[-.5,     .5,     .5,    -.5],
                          [-.5,    -.5,     .5,     .5],
                          [ .0,     .0,     .0,     .0],
                          [ 1.,     1.,     1.,     1.]])

        tx, ty, tw, th = self.texcoords
        sx, sy = self.rescale
        width = override_width or (tw * sx)
        height = override_height or (th * sy)

        vertmat.scale(width, height, 1.)
        if self.mirrored:
            vertmat.flip()
        if self.rotations_3d != (0., 0., 0.):
            rx, ry, rz = self.rotations_3d
            if rx:
                vertmat.rotate_x(-rx)
            if ry:
                vertmat.rotate_y(ry)
            if rz:
                vertmat.rotate_z(-rz) #TODO: minus, really?
        if self.corner_relative_placement: # Reposition
            vertmat.translate(width / 2., height / 2., 0.)

        uvs = [(tx / self.anm.size[0],         1. - (ty / self.anm.size[1])),
               ((tx + tw) / self.anm.size[0],  1. - (ty / self.anm.size[1])),
               ((tx + tw) / self.anm.size[0],  1. - ((ty + th) / self.anm.size[1])),
               (tx / self.anm.size[0],         1. - ((ty + th) / self.anm.size[1]))]

        vertices = []
        for i in xrange(4):
            w = vertmat.data[3][i]
            vertices.append((vertmat.data[0][i] / w,
                             vertmat.data[1][i] / w,
                             vertmat.data[2][i] / w))

        self._uvs, self._vertices = uvs, vertices



    def update(self):
        properties = {}
        for time, instr_type, data in self.anm.scripts[self.script_index]:
            if time == self.frame:
                if instr_type == 15: #Return
                    break
                else:
                    properties[instr_type] = data
        self.frame += 1

        self.rotations_3d = tuple(x + y for x, y in zip(self.rotations_3d, self.rotations_speed_3d))

        if properties:
            if 1 in properties:
                self.texcoords = self.anm.sprites[unpack('<I', properties[1])[0]]
                del properties[1]
            if 2 in properties:
                self.rescale = unpack('<ff', properties[2])
                del properties[2]
            if 5 in properties:
                self.frame, = unpack('<I', properties[5])
                del properties[5]
            if 7 in properties:
                self.mirrored = True #TODO
                del properties[7]
            if 9 in properties:
                self.rotations_3d = unpack('<fff', properties[9])
                del properties[9]
            if 10 in properties:
                self.rotations_speed_3d = unpack('<fff', properties[10])
                del properties[10]
            if 23 in properties:
                self.corner_relative_placement = True #TODO
                del properties[23]
            if properties:
                print('Leftover properties: %r' % properties) #TODO
            return True
        if self.rotations_speed_3d != (0., 0., 0.):
            return True
        return False

