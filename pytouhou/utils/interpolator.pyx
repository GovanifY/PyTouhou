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

from libc.stdlib cimport malloc, free


cdef class Interpolator:
    def __init__(self, tuple values, unsigned long start_frame=0, tuple end_values=None,
                 unsigned long end_frame=0, formula=None):
        self._length = len(values)
        self._values = <double*>malloc(self._length * sizeof(double))
        self.start_values = <double*>malloc(self._length * sizeof(double))
        self.end_values = <double*>malloc(self._length * sizeof(double))
        for i in range(self._length):
            self._values[i] = values[i]
            self.start_values[i] = self._values[i]
        if end_values is not None:
            for i in range(self._length):
                self.end_values[i] = end_values[i]
        self.start_frame = start_frame
        self.end_frame = end_frame
        self._frame = 0
        self._formula = formula


    def __dealloc__(self):
        free(self.end_values)
        free(self.start_values)
        free(self._values)


    property values:
        def __get__(self):
            return tuple([self._values[i] for i in range(self._length)])


    def __nonzero__(self):
        return self._frame < self.end_frame


    cpdef set_interpolation_start(self, unsigned long frame, tuple values):
        for i in range(self._length):
            self.start_values[i] = values[i]
        self.start_frame = frame


    cpdef set_interpolation_end(self, unsigned long frame, tuple values):
        for i in range(self._length):
            self.end_values[i] = values[i]
        self.end_frame = frame


    cpdef set_interpolation_end_frame(self, unsigned long end_frame):
        self.end_frame = end_frame


    cpdef set_interpolation_end_values(self, tuple values):
        for i in range(self._length):
            self.end_values[i] = values[i]


    cpdef update(self, unsigned long frame):
        cdef double coeff

        self._frame = frame
        if frame + 1 >= self.end_frame: #XXX: skip the last interpolation step
            # This bug is replicated from the original game
            for i in range(self._length):
                self._values[i] = self.end_values[i]
                self.start_values[i] = self.end_values[i]
            self.start_frame = frame
        else:
            coeff = float(frame - self.start_frame) / float(self.end_frame - self.start_frame)
            if self._formula is not None:
                coeff = self._formula(coeff)
            for i in range(self._length):
                start_value = self.start_values[i]
                end_value = self.end_values[i]
                self._values[i] = start_value + coeff * (end_value - start_value)
