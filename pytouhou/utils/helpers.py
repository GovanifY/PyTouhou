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

#TODO: remove that someday.
from logging import getLogger as get_logger


def read_string(file, size, encoding=None):
    data = file.read(size)

    try:
        data = data[:data.index(b'\x00')]
    except ValueError:
        pass

    if encoding:
        return data.decode(encoding)
    else:
        return data

