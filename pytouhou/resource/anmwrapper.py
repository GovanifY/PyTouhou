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

from itertools import repeat, chain


class AnmWrapper(object):
    def __init__(self, anm_files, offsets=None):
        """Wrapper for scripts and sprites described in “anm_files”.

        The optional “offsets” argument specifies a list of offsets to be added
        to script and sprite numbers of each file described in “anm_files”.

        That is, if anm_files[0] and anm_files[1] each have only one sprite,
        numbered 0 in both cases, and offsets=(0, 1), the first file's sprite
        will be numbered 0 and the second file's will be numbered 1.
        """
        self.scripts = {}
        self.sprites = {}

        if not offsets:
            offsets = repeat(0) # “offsets” defaults to zeroes

        for anm, offset in zip(chain(*anm_files), offsets):
            for script_id, script in anm.scripts.iteritems():
                self.scripts[script_id + offset] = (anm, script) #TODO: check
            for sprite_id, sprite in anm.sprites.iteritems():
                self.sprites[sprite_id + offset] = (anm, sprite)


    def get_sprite(self, sprite_index):
        return self.sprites[sprite_index]


    def get_script(self, script_index):
        return self.scripts[script_index]

