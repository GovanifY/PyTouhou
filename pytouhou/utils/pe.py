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

from struct import Struct, unpack
from collections import namedtuple


class PEStructs:
    _IMAGE_FILE_HEADER = namedtuple('_IMAGE_FILE_HEADER',
                                    ('Machine',
                                     'NumberOfSections',
                                     'TimeDateStamp',
                                     'PointerToSymbolTable',
                                     'NumberOfSymbols',
                                     'SizeOfOptionalHeader',
                                     'Characteristics'))
    @classmethod
    def read_image_file_header(cls, file):
        format = Struct('<HHIIIHH')
        return cls._IMAGE_FILE_HEADER(*format.unpack(file.read(format.size)))

    _IMAGE_OPTIONAL_HEADER = namedtuple('_IMAGE_OPTIONAL_HEADER',
                                        ('Magic',
                                         'MajorLinkerVersion', 'MinorLinkerVersion',
                                         'SizeOfCode', 'SizeOfInitializedData',
                                         'SizeOfUninitializedData',
                                         'AddressOfEntryPoint', 'BaseOfCode',
                                         'BaseOfData', 'ImageBase',
                                         'SectionAlignement', 'FileAlignement',
                                         'MajorOperatingSystemVersion',
                                         'MinorOperatingSystemVersion',
                                         'MajorImageVersion',
                                         'MinorImageVersion',
                                         'MajorSubsystemVersion',
                                         'MinorSubsystemVersion',
                                         'Win32VersionValue',
                                         'SizeOfImage',
                                         'SizeOfHeaders',
                                         'CheckSum',
                                         'Subsystem',
                                         'DllCharacteristics',
                                         'SizeOfStackReserve',
                                         'SizeOfStackCommit',
                                         'SizeOfHeapReserve',
                                         'SizeOfHeapCommit',
                                         'LoaderFlags',
                                         'NumberOfRvaAndSizes',
                                         'DataDirectory'))
    _IMAGE_DATA_DIRECTORY = namedtuple('_IMAGE_DATA_DIRECTORY',
                                       ('VirtualAddress', 'Size'))
    @classmethod
    def read_image_optional_header(cls, file):
        format = Struct('<HBBIIIIIIIIIHHHHHHIIIIHHIIIIII')
        directory_format = Struct('<II')
        directory = []
        partial_header = format.unpack(file.read(format.size))
        directory = [cls._IMAGE_DATA_DIRECTORY(*directory_format.unpack(file.read(directory_format.size))) for i in range(16)]
        return cls._IMAGE_OPTIONAL_HEADER(*(partial_header + (directory,)))

    _IMAGE_SECTION_HEADER = namedtuple('_IMAGE_SECTION_HEADER',
                                       ('Name', 'VirtualSize',
                                        'VirtualAddress',
                                        'SizeOfRawData', 'PointerToRawData',
                                        'PointerToRelocations',
                                        'PointerToLinenumbers',
                                        'NumberOfRelocations',
                                        'NumberOfLinenumbers',
                                        'Characteristics'))
    @classmethod
    def read_image_section_header(cls, file):
        format = Struct('<8sIIIIIIHHI')
        return cls._IMAGE_SECTION_HEADER(*format.unpack(file.read(format.size)))



class PEFile:
    def __init__(self, file):
        self.file = file

        self.image_base = 0
        self.sections = []

        file.seek(0x3c)
        pe_offset, = unpack('<I', file.read(4))

        file.seek(pe_offset)
        pe_sig = file.read(4)
        assert pe_sig == b'PE\0\0'

        pe_file_header = PEStructs.read_image_file_header(file)
        pe_optional_header = PEStructs.read_image_optional_header(file)

        # Read image base
        self.image_base = pe_optional_header.ImageBase

        self.sections = [PEStructs.read_image_section_header(file)
                            for i in range(pe_file_header.NumberOfSections)]


    def seek_to_va(self, va):
        self.file.seek(self.va_to_offset(va))


    def offset_to_rva(self, offset):
        for section in self.sections:
            if 0 <= (offset - section.PointerToRawData) < section.SizeOfRawData:
                #TODO: is that okay?
                return offset - section.PointerToRawData + section.VirtualAddress
        raise IndexError #TODO


    def offset_to_va(self, offset):
        return self.offset_to_rva(offset) + self.image_base


    def rva_to_offset(self, rva):
        for section in self.sections:
            if 0 <= (rva - section.VirtualAddress) < section.SizeOfRawData:
                #TODO: is that okay?
                return rva - section.VirtualAddress + section.PointerToRawData
        raise IndexError #TODO


    def va_to_offset(self, va):
        return self.rva_to_offset(va - self.image_base)

