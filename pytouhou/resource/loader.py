# -*- encoding: utf-8 -*-
##
## Copyright (C) 2012 Thibaut Girka <thib@sitedethib.com>
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

import os
from glob import glob
from itertools import chain
from io import BytesIO

from pytouhou.formats import WrongFormatError
from pytouhou.formats.pbg3 import PBG3
from pytouhou.formats.std import Stage
from pytouhou.formats.ecl import ECL
from pytouhou.formats.anm0 import ANM0
from pytouhou.formats.msg import MSG
from pytouhou.formats.sht import SHT
from pytouhou.formats.exe import SHT as EoSDSHT, InvalidExeException
from pytouhou.formats.music import Track
from pytouhou.formats.fmt import FMT


from pytouhou.resource.anmwrapper import AnmWrapper

from pytouhou.utils.helpers import get_logger

logger = get_logger(__name__)



class Directory(object):
    def __init__(self, path):
        self.path = path


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        return False


    def list_files(self):
        file_list = []
        for path in os.listdir(self.path):
            if os.path.isfile(os.path.join(self.path, path)):
                file_list.append(path)
        return file_list


    def extract(self, name):
        with open(os.path.join(self.path, str(name)), 'rb') as file:
            contents = file.read()
        return contents



class ArchiveDescription(object):
    _formats = {'PBG3': PBG3}

    def __init__(self, path, format_class, file_list=None):
        self.path = path
        self.format_class = format_class
        self.file_list = file_list or []


    def open(self):
        if self.format_class is Directory:
            return self.format_class(self.path)

        file = open(self.path, 'rb')
        instance = self.format_class.read(file)
        return instance


    @classmethod
    def get_from_path(cls, path):
        if os.path.isdir(path):
            instance = Directory(path)
            file_list = instance.list_files()
            return cls(path, Directory, file_list)
        with open(path, 'rb') as file:
            magic = file.read(4)
            file.seek(0)
            format_class = cls._formats[magic]
            instance = format_class.read(file)
            file_list = instance.list_files()
        return cls(path, format_class, file_list)



class Loader(object):
    def __init__(self, game_dir=None):
        self.exe_files = []
        self.game_dir = game_dir
        self.known_files = {}
        self.instanced_anms = {} #TODO: remove it someday.


    def scan_archives(self, paths_lists):
        for paths in paths_lists:
            def _expand_paths():
                for path in paths.split(os.path.pathsep):
                    if self.game_dir and not os.path.isabs(path):
                        path = os.path.join(self.game_dir, path)
                    yield glob(path)
            paths = list(chain(*_expand_paths()))
            if not paths:
                raise IOError
            path = paths[0]
            if os.path.splitext(path)[1] == '.exe':
                self.exe_files.extend(paths)
            else:
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
            self.instanced_anms[name] = ANM0.read(file)
        return self.instanced_anms[name]


    def get_stage(self, name):
        file = self.get_file(name)
        return Stage.read(file) #TODO: modular


    def get_ecl(self, name):
        file = self.get_file(name)
        return ECL.read(file) #TODO: modular


    def get_msg(self, name):
        file = self.get_file(name)
        return MSG.read(file) #TODO: modular


    def get_sht(self, name):
        file = self.get_file(name)
        return SHT.read(file) #TODO: modular


    def get_eosd_characters(self):
        #TODO: Move to pytouhou.games.eosd?
        for path in self.exe_files:
            try:
                with open(path, 'rb') as file:
                    characters = EoSDSHT.read(file)
                return characters
            except InvalidExeException:
                pass
        logger.error("Required game exe not found!")


    def get_track(self, name):
        posname = name.replace('bgm/', '').replace('.mid', '.pos')
        file = self.get_file(posname)
        return Track.read(file) #TODO: modular


    def get_fmt(self, name):
        file = self.get_file(name)
        return FMT.read(file) #TODO: modular


    def get_anm_wrapper(self, names, offsets=None):
        """Create an AnmWrapper for ANM files “names”.

        If one of the files “names” does not exist or is not a valid ANM file,
        raises an exception.
        """
        return AnmWrapper((self.get_anm(name) for name in names), offsets)


    def get_anm_wrapper2(self, names, offsets=None):
        """Create an AnmWrapper for ANM files “names”.

        Stop at the first non-existent or invalid ANM file if there is one,
        and return an AnmWrapper for all the previous correct files.
        """
        anms = []

        try:
            for name in names:
                anms.append(self.get_anm(name))
        except KeyError:
            pass

        return AnmWrapper(anms, offsets)

