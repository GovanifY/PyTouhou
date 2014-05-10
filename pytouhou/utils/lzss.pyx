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

cimport cython
from libc.stdlib cimport calloc, malloc, free

from .bitstream cimport BitStream


@cython.cdivision(True)
cpdef bytes decompress(BitStream bitstream,
                       Py_ssize_t size,
                       unsigned int dictionary_size=0x2000,
                       unsigned int offset_size=13,
                       unsigned int length_size=4,
                       unsigned int minimum_match_length=3):
    cdef Py_ssize_t ptr, length
    cdef unsigned int dictionary_head
    cdef unsigned char byte
    cdef char *out_data
    cdef char *dictionary

    out_data = <char*> malloc(size)
    dictionary = <char*> calloc(dictionary_size, 1)
    dictionary_head, ptr = 1, 0

    while ptr < size:
        if bitstream.read_bit():
            # The `flag` bit is set, indicating the upcoming chunk of data is a literal
            # Add it to the uncompressed file, and store it in the dictionary
            byte = bitstream.read(8)
            dictionary[dictionary_head] = byte
            dictionary_head = (dictionary_head + 1) % dictionary_size
            out_data[ptr] = byte
            ptr += 1
        else:
            # The `flag` bit is not set, the upcoming chunk is a (offset, length) tuple
            offset = bitstream.read(offset_size)
            length = bitstream.read(length_size) + minimum_match_length
            if ptr + length > size:
                raise Exception
            if offset == 0 and length == 0:
                break
            for i in range(offset, offset + length):
                out_data[ptr] = dictionary[i % dictionary_size]
                dictionary[dictionary_head] = dictionary[i % dictionary_size]
                dictionary_head = (dictionary_head + 1) % dictionary_size
                ptr += 1

    _out_data = out_data[:size]
    free(out_data)
    free(dictionary)
    return _out_data

