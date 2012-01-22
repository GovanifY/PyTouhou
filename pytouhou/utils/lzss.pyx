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

from libc.stdlib cimport calloc, malloc, free


cpdef bytes decompress(object bitstream,
                       Py_ssize_t size,
                       unsigned int dictionary_size=0x2000,
                       unsigned int offset_size=13,
                       unsigned int length_size=4,
                       unsigned int minimum_match_length=3):
    cdef unsigned int i, ptr, dictionary_head, offset, length
    cdef unsigned char flag, byte, *out_data, *dictionary
    cdef bytes _out_data

    out_data = <unsigned char*> malloc(size)
    dictionary = <unsigned char*> calloc(dictionary_size, 1)
    dictionary_head, ptr = 1, 0

    while ptr < size:
        flag = bitstream.read_bit()
        if flag:
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
            if offset == 0 and length == 0:
                break
            for i in range(offset, offset + length):
                out_data[ptr % size] = dictionary[i % dictionary_size]
                ptr += 1
                dictionary[dictionary_head] = dictionary[i % dictionary_size]
                dictionary_head = (dictionary_head + 1) % dictionary_size

    _out_data = out_data[:size]
    free(out_data)
    free(dictionary)
    return _out_data

