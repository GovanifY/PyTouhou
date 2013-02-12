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

from pyglet.gl import (glClear, glMatrixMode, glLoadIdentity, glLoadMatrixf,
                       glDisable, glEnable, glFogi, glFogf, glFogfv,
                       GL_DEPTH_BUFFER_BIT, GL_PROJECTION, GL_MODELVIEW,
                       GL_FOG, GL_FOG_MODE, GL_LINEAR, GL_FOG_START,
                       GL_FOG_END, GL_FOG_COLOR, GL_COLOR_BUFFER_BIT, GLfloat)

from pytouhou.utils.matrix import Matrix

from .renderer import Renderer



class GameRenderer(Renderer):
    __slots__ = ('game', 'background')

    def __init__(self, resource_loader, game=None, background=None):
        Renderer.__init__(self, resource_loader)
        if game:
            self.load_game(game, background)


    def load_game(self, game=None, background=None):
        self.game = game
        self.background = background

        if game:
            # Preload textures
            self.texture_manager.preload(game.resource_loader.instanced_anms.values())


    def render(self):
        glClear(GL_DEPTH_BUFFER_BIT)

        back = self.background
        game = self.game

        if self.use_fixed_pipeline:
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()

        if game is not None and game.spellcard_effect is not None:
            if self.use_fixed_pipeline:
                glMatrixMode(GL_MODELVIEW)
                glLoadMatrixf(self.game_mvp.get_c_data())
                glDisable(GL_FOG)
            else:
                self.game_shader.bind()
                self.game_shader.uniform_matrixf('mvp', self.game_mvp.get_c_data())

            self.render_elements([game.spellcard_effect])
        elif back is not None:
            if self.use_fixed_pipeline:
                glEnable(GL_FOG)
            else:
                self.background_shader.bind()
            fog_b, fog_g, fog_r, fog_start, fog_end = back.fog_interpolator.values
            x, y, z = back.position_interpolator.values
            dx, dy, dz = back.position2_interpolator.values

            glFogi(GL_FOG_MODE, GL_LINEAR)
            glFogf(GL_FOG_START, fog_start)
            glFogf(GL_FOG_END,  fog_end)
            glFogfv(GL_FOG_COLOR, (GLfloat * 4)(fog_r / 255., fog_g / 255., fog_b / 255., 1.))

            model = Matrix()
            model.data[3] = [-x, -y, -z, 1]
            view = self.setup_camera(dx, dy, dz)

            if self.use_fixed_pipeline:
                model_view_projection = model * view * self.proj
                glMatrixMode(GL_MODELVIEW)
                glLoadMatrixf(model_view_projection.get_c_data())
            else:
                model_view = model * view
                self.background_shader.uniform_matrixf('model_view', model_view.get_c_data())
                self.background_shader.uniform_matrixf('projection', self.proj.get_c_data())

            self.render_background(back)
        else:
            glClear(GL_COLOR_BUFFER_BIT)

        if game is not None:
            if self.use_fixed_pipeline:
                glMatrixMode(GL_MODELVIEW)
                glLoadMatrixf(self.game_mvp.get_c_data())
                glDisable(GL_FOG)
            else:
                self.game_shader.bind()
                self.game_shader.uniform_matrixf('mvp', self.game_mvp.get_c_data())

            self.render_elements(enemy for enemy in game.enemies if enemy.visible)
            self.render_elements(game.effects)
            self.render_elements(chain(game.players_bullets,
                                       game.lasers_sprites(),
                                       game.players,
                                       game.msg_sprites()))
            self.render_elements(chain(game.bullets, game.lasers,
                                       game.cancelled_bullets, game.items,
                                       game.labels))
