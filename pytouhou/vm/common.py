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


class MetaRegistry(type):
    def __new__(mcs, name, bases, classdict):
        instruction_handlers = {}
        for item in classdict.itervalues():
            try:
                instruction_ids = item._instruction_ids
            except AttributeError:
                pass
            else:
                for id_ in instruction_ids:
                    instruction_handlers[id_] = item
        classdict['_handlers'] = instruction_handlers
        return type.__new__(mcs, name, bases, classdict)



def instruction(instruction_id):
    def _decorator(func):
        if not hasattr(func, '_instruction_ids'):
            func._instruction_ids = set()
        func._instruction_ids.add(instruction_id)
        return func
    return _decorator
