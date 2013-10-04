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

"""PBG3 archive files handling.

This module provides classes for handling the PBG3 file format.
The PBG3 format is the archive format used by Touhou: EoSD.

PBG3 files are merely a bitstream composed of a header,
a file table, and LZSS-compressed files.
"""

from collections import namedtuple

from pytouhou.utils.bitstream import BitStream
from pytouhou.utils import lzss

from pytouhou.utils.helpers import get_logger

from pytouhou.formats import WrongFormatError

logger = get_logger(__name__)


class PBG3BitStream(BitStream):
    """Helper class to handle strings and integers in PBG3 bitstreams."""

    def read_int(self):
        """Read an integer from the bitstream.

        Integers have variable sizes. They begin with a two-bit value indicating
        the number of (non-aligned) bytes to read.
        """

        size = self.read(2)
        return self.read((size + 1) * 8)


    def read_string(self, maxsize):
        """Read a string from the bitstream.

        Strings are stored as standard NULL-termianted sequences of bytes.
        The only catch is that they are not byte-aligned.
        """

        string = []
        for i in range(maxsize):
            byte = self.read(8)
            if byte == 0:
                break
            string.append(byte)
        return ''.join(chr(byte) for byte in string)



PBG3Entry = namedtuple('PBG3Entry', 'unknown1 unknown2 checksum offset size')



class PBG3(object):
    """Handle PBG3 archive files.

    PBG3 is a file archive format used in Touhou 6: EoSD.
    This class provides a representation of such files, as well as functions to
    read and extract files from a PBG3 archive.

    Instance variables:
    entries -- list of PBG3Entry objects describing files present in the archive
    bitstream -- PBG3BitStream object
    """

    def __init__(self, entries=None, bitstream=None):
        self.entries = entries or {}
        self.bitstream = bitstream #TODO


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        return self.bitstream.__exit__(type, value, traceback)


    @classmethod
    def read(cls, file):
        """Read a PBG3 file.

        Raise an exception if the file is invalid.
        Return a PBG3 instance otherwise.
        """

        magic = file.read(4)
        if magic != b'PBG3':
            raise WrongFormatError(magic)

        bitstream = PBG3BitStream(file)
        entries = {}

        nb_entries = bitstream.read_int()
        offset = bitstream.read_int()
        bitstream.seek(offset)
        for i in range(nb_entries):
            unknown1 = bitstream.read_int()
            unknown2 = bitstream.read_int()
            checksum = bitstream.read_int() # Checksum of *compressed data*
            offset = bitstream.read_int()
            size = bitstream.read_int()
            name = bitstream.read_string(255).decode('ascii')
            entries[name] = PBG3Entry(unknown1, unknown2, checksum, offset, size)

        return PBG3(entries, bitstream)


    def list_files(self):
        """List files present in the archive."""
        return self.entries.keys()


    def extract(self, filename, check=False):
        """Extract a given file.

        If “filename” is in the archive, extract it and return its contents.
        Otherwise, raise an exception.

        By default, the checksum of the file won't be verified,
        you can however force the verification using the “check” argument.
        """

        unkwn1, unkwn2, checksum, offset, size = self.entries[filename]
        self.bitstream.seek(offset)
        data = lzss.decompress(self.bitstream, size)
        if check:
            # Verify the checksum
            compressed_size = self.bitstream.io.tell() - offset
            self.bitstream.seek(offset)
            value = 0
            for c in self.bitstream.io.read(compressed_size):
                value += ord(c)
                value &= 0xFFFFFFFF
            if value != checksum:
                logger.warn('corrupted data!')
        return data

