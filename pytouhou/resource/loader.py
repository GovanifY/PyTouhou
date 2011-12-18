from io import BytesIO

from pytouhou.formats.pbg3 import PBG3
from pytouhou.formats.std import Stage
from pytouhou.formats.ecl import ECL
from pytouhou.formats.anm0 import Animations
from pytouhou.formats.msg import MSG
from pytouhou.formats.sht import SHT


from pytouhou.resource.anmwrapper import AnmWrapper


class ArchiveDescription(object):
    _formats = {'PBG3': PBG3}

    def __init__(self, path, format_class, file_list=None):
        self.path = path
        self.format_class = format_class
        self.file_list = file_list or []


    def open(self):
        file = open(self.path, 'rb')
        instance = self.format_class.read(file)
        return instance


    @classmethod
    def get_from_path(cls, path):
        with open(path, 'rb') as file:
            magic = file.read(4)
            file.seek(0)
            format_class = cls._formats[magic]
            instance = format_class.read(file)
            file_list = instance.list_files()
        return cls(path, format_class, file_list)



class Loader(object):
    def __init__(self):
        self.known_files = {}
        self.instanced_ecls = {}
        self.instanced_anms = {}
        self.instanced_stages = {}
        self.instanced_msgs = {}
        self.instanced_shts = {}


    def scan_archives(self, paths):
        for path in paths:
            archive_description = ArchiveDescription.get_from_path(path)
            for name in archive_description.file_list:
                self.known_files[name] = archive_description


    def get_file_data(self, name):
        with self.known_files[name].open() as archive:
            content = archive.extract(name)
        return content


    def get_file(self, name):
        with self.known_files[name].open() as archive:
            content = archive.extract(name)
        return BytesIO(content)


    def get_anm(self, name):
        if name not in self.instanced_anms:
            file = self.get_file(name)
            self.instanced_anms[name] = Animations.read(file) #TODO: modular
        return self.instanced_anms[name]


    def get_stage(self, name):
        if name not in self.instanced_stages:
            file = self.get_file(name)
            self.instanced_stages[name] = Stage.read(file) #TODO: modular
        return self.instanced_stages[name]


    def get_ecl(self, name):
        if name not in self.instanced_ecls:
            file = self.get_file(name)
            self.instanced_ecls[name] = ECL.read(file) #TODO: modular
        return self.instanced_ecls[name]


    def get_msg(self, name):
        if name not in self.instanced_msgs:
            file = self.get_file(name)
            self.instanced_msgs[name] = MSG.read(file) #TODO: modular
        return self.instanced_msgs[name]


    def get_sht(self, name):
        if name not in self.instanced_shts:
            file = self.get_file(name)
            self.instanced_shts[name] = SHT.read(file) #TODO: modular
        return self.instanced_shts[name]


    def get_anm_wrapper(self, names):
        return AnmWrapper(self.get_anm(name) for name in names)


    def get_anm_wrapper2(self, names):
        anims = []
        try:
            for name in names:
                anims.append(self.get_anm(name))
        except KeyError:
            pass

        return AnmWrapper(anims)

