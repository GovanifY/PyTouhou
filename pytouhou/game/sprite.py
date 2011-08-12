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
        self.corner_relative_placement = False
        self.frame = 0
        self._uvs = []
        self._vertices = []


    def update_uvs_vertices(self, override_width=0, override_height=0):
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

        tx, ty, tw, th = self.texcoords
        sx, sy = self.rescale
        width = override_width or (tw * sx)
        height = override_height or (th * sy)

        transform = Matrix.get_scaling_matrix(width, height, 1.)
        if self.mirrored:
            transform = Matrix.get_scaling_matrix(-1., 1., 1.).mult(transform)
        if self.rotations_3d != (0., 0., 0.):
            rx, ry, rz = self.rotations_3d
            transform = Matrix.get_rotation_matrix(-rx, 'x').mult(transform)
            transform = Matrix.get_rotation_matrix(ry, 'y').mult(transform)
            transform = Matrix.get_rotation_matrix(-rz, 'z').mult(transform) #TODO: minus, really?
        if self.corner_relative_placement: # Reposition
            transform = Matrix.get_translation_matrix(width / 2., height / 2., 0.).mult(transform)
        vertmat = transform.mult(vertmat)

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



    def update(self, override_width=0, override_height=0):
        properties = {}
        for time, instr_type, data in self.anm.scripts[self.script_index]:
            if time == self.frame:
                if instr_type == 15: #Return
                    break
                else:
                    properties[instr_type] = data
        self.frame += 1

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
            if 23 in properties:
                self.corner_relative_placement = True #TODO
                del properties[23]
            if properties:
                print('Leftover properties: %r' % properties) #TODO
            self.update_uvs_vertices(override_width, override_height)
            return True
        return False

