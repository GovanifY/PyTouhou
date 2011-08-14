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
        self.instruction_pointer = 0
        self.keep_still = False
        self.playing = True
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

        vertmat.scale2d(width, height)
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

        x_1 = 1. / self.anm.size[0]
        y_1 = 1. / self.anm.size[1]
        uvs = [(tx * x_1,         1. - (ty * y_1)),
               ((tx + tw) * x_1,  1. - (ty * y_1)),
               ((tx + tw) * x_1,  1. - ((ty + th) * y_1)),
               (tx * x_1,         1. - ((ty + th) * y_1))]

        d = vertmat.data
        assert (d[3][0], d[3][1], d[3][2], d[3][3]) == (1., 1., 1., 1.)
        self._uvs, self._vertices = uvs, zip(d[0], d[1], d[2])



    def update(self):
        if not self.playing:
            return False

        changed = False
        frame = self.frame
        if not self.keep_still:
            script = self.anm.scripts[self.script_index]
            try:
                while frame <= self.frame:
                    frame, instr_type, data = script[self.instruction_pointer]
                    if frame == self.frame:
                        changed = True
                        if instr_type == 1:
                            self.texcoords = self.anm.sprites[unpack('<I', data)[0]]
                        elif instr_type == 2:
                            self.rescale = unpack('<ff', data)
                        elif instr_type == 5:
                            self.frame, = unpack('<I', data)
                            self.instruction_pointer = 0
                        elif instr_type == 7:
                            self.mirrored = True
                        elif instr_type == 9:
                            self.rotations_3d = unpack('<fff', data)
                        elif instr_type == 10:
                            self.rotations_speed_3d = unpack('<fff', data)
                        elif instr_type == 23:
                            self.corner_relative_placement = True #TODO
                        elif instr_type == 15:
                            self.keep_still = True
                            break
                        else:
                            print('unhandled opcode: %d, %r' % (instr_type, data)) #TODO
                    if frame <= self.frame:
                        self.instruction_pointer += 1
            except IndexError:
                self.playing = False
                pass
        self.frame += 1

        ax, ay, az = self.rotations_3d
        sax, say, saz = self.rotations_speed_3d
        self.rotations_3d = ax + sax, ay + say, az + saz

        if self.rotations_speed_3d != (0., 0., 0.):
            return True

        return changed

