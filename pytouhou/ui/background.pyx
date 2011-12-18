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

#TODO: lots of things

from struct import pack
from itertools import chain

from .sprite cimport get_sprite_rendering_data

cpdef object get_background_rendering_data(object background):
    cdef float x, y, z, ox, oy, oz, ox2, oy2, oz2
    cdef list vertices, uvs, colors

    #TODO: do not cache the results, and use view frustum culling
    try:
        return background._rendering_data
    except AttributeError:
        pass

    vertices = []
    uvs = []
    colors = []

    for ox, oy, oz, model_id, model in background.object_instances:
        for ox2, oy2, oz2, width_override, height_override, sprite in model:
            #TODO: view frustum culling
            key, (vertices2, uvs2, colors2) = get_sprite_rendering_data(sprite)
            vertices.extend([(x + ox + ox2, y + oy + oy2, z + oz + oz2)
                                for x, y, z in vertices2])
            uvs.extend(uvs2)
            colors.extend(colors2)

    nb_vertices = len(vertices)
    vertices_s = pack(str(3 * nb_vertices) + 'f', *chain(*vertices))
    uvs_s = pack(str(2 * nb_vertices) + 'f', *uvs)
    colors_s = pack(str(4 * nb_vertices) + 'B', *colors)

    background._rendering_data = [(key, (nb_vertices, vertices_s, uvs_s, colors_s))]

    return background._rendering_data

