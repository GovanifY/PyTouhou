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
        for item in classdict.values():
            if hasattr(item, '_instruction_ids'):
                for version, instruction_ids in item._instruction_ids.items():
                    for id_ in instruction_ids:
                        instruction_handlers.setdefault(version, {})[id_] = item
        classdict['_handlers'] = instruction_handlers
        return type.__new__(mcs, name, bases, classdict)



def instruction(instruction_id, version=6):
    def _decorator(func):
        if not hasattr(func, '_instruction_ids'):
            func._instruction_ids = {}
        func._instruction_ids.setdefault(version, set()).add(instruction_id)
        return func
    return _decorator
