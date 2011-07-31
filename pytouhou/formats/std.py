from struct import pack, unpack
from pytouhou.utils.helpers import read_string



class Object(object):
    def __init__(self):
        self.header = (b'\x00') * 28 #TODO
        self.quads = []



class Stage(object):
    def __init__(self):
        self.name = ''
        self.bgms = (('', ''), ('', ''), ('', ''))
        self.objects = []
        self.object_instances = []
        self.script = []


    @classmethod
    def read(cls, file):
        stage = Stage()

        nb_objects, nb_faces = unpack('<HH', file.read(4))
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

        # Read object definitions
        offsets = unpack('<%s' % ('I' * nb_objects), file.read(4 * nb_objects))
        for offset in offsets:
            obj = Object()
            obj.header = file.read(28) #TODO: this has to be reversed!
            while True:
                unknown, size = unpack('<HH', file.read(4))
                if unknown == 0xffff:
                    break
                if size != 0x1c:
                    raise Exception #TODO
                script_index, _padding, x, y, z, width, height = unpack('<HHfffff', file.read(24))
                #TODO: store script_index, x, y, z, width and height
                obj.quads.append((script_index, x, y, z, width, height))
            stage.objects.append(obj)


        # Read object usages
        file.seek(object_instances_offset)
        while True:
            obj_id, unknown, x, y, z = unpack('<HHfff', file.read(16))
            if (obj_id, unknown) == (0xffff, 0xffff):
                break
            if unknown != 256:
                raise Exception #TODO
            stage.object_instances.append((stage.objects[obj_id], x, y, z))


        # Read other funny things (script)
        file.seek(script_offset)
        while True:
            frame, message_type, size = unpack('<IHH', file.read(8))
            if (frame, message_type, size) == (0xffffffff, 0xffff, 0xffff):
                break
            if size != 0x0c:
                raise Exception #TODO
            data = file.read(12)
            #TODO: do something useful with this

        return stage

