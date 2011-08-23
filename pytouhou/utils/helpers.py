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


from logging import StreamHandler, Formatter, getLogger


def get_logger(name):
    handler = StreamHandler()
    formatter = Formatter(fmt='[%(name)s] [%(levelname)s]: %(message)s')
    handler.setFormatter(formatter)
    logger = getLogger(name)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


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

