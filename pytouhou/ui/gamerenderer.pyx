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


from itertools import chain

from pyglet.gl import *

from .renderer cimport Renderer
from .background cimport get_background_rendering_data



cdef class GameRenderer(Renderer):
    cdef public game
    cdef public background


    def __init__(self, resource_loader, game=None, background=None):
        Renderer.__init__(self, resource_loader)
        if game:
            self.load_game(game, background)


    cpdef load_game(self, game=None, background=None):
        self.game = game
        self.background = background

        if game:
            # Preload textures
            self.texture_manager.preload(game.resource_loader.instanced_anms.values())


    def render(self):
        glClear(GL_DEPTH_BUFFER_BIT)

        back = self.background
        game = self.game
        texture_manager = self.texture_manager

        if game is not None and game.spellcard_effect is not None:
            self.setup_camera(0, 0, 1)

            glDisable(GL_FOG)
            self.render_elements([game.spellcard_effect])
            glEnable(GL_FOG)
        elif back is not None:
            fog_b, fog_g, fog_r, fog_start, fog_end = back.fog_interpolator.values
            x, y, z = back.position_interpolator.values
            dx, dy, dz = back.position2_interpolator.values

            glFogi(GL_FOG_MODE, GL_LINEAR)
            glFogf(GL_FOG_START, fog_start)
            glFogf(GL_FOG_END,  fog_end)
            glFogfv(GL_FOG_COLOR, (GLfloat * 4)(fog_r / 255., fog_g / 255., fog_b / 255., 1.))

            self.setup_camera(dx, dy, dz)
            glTranslatef(-x, -y, -z)

            glEnable(GL_DEPTH_TEST)
            for (texture_key, blendfunc), (nb_vertices, vertices, uvs, colors) in get_background_rendering_data(back):
                glBlendFunc(GL_SRC_ALPHA, (GL_ONE_MINUS_SRC_ALPHA, GL_ONE)[blendfunc])
                glBindTexture(GL_TEXTURE_2D, texture_manager[texture_key].id)
                glVertexPointer(3, GL_FLOAT, 0, vertices)
                glTexCoordPointer(2, GL_FLOAT, 0, uvs)
                glColorPointer(4, GL_UNSIGNED_BYTE, 0, colors)
                glDrawArrays(GL_QUADS, 0, nb_vertices)
            glDisable(GL_DEPTH_TEST)
        else:
            glClear(GL_COLOR_BUFFER_BIT)

        if game is not None:
            self.setup_camera(0, 0, 1)

            glDisable(GL_FOG)
            self.render_elements(chain(*(enemy.objects() for enemy in game.enemies if enemy.visible)))
            self.render_elements(enemy for enemy in game.enemies if enemy.visible)
            self.render_elements(game.effects)
            self.render_elements(chain(game.players_bullets,
                                       game.lasers_sprites(),
                                       game.players,
                                       game.msg_sprites(),
                                       *(player.objects() for player in game.players)))
            self.render_elements(chain(game.bullets, game.lasers,
                                       game.cancelled_bullets, game.items,
                                       (item.indicator for item in game.items if item.indicator),
                                       *(label.objects() for label in game.labels)))
            glEnable(GL_FOG)

