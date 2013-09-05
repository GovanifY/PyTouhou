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

from pytouhou.lib.opengl cimport \
         (glClear, glMatrixMode, glLoadIdentity, glLoadMatrixf, glDisable,
          glEnable, glFogi, glFogf, glFogfv,
          GL_PROJECTION, GL_MODELVIEW, GL_FOG, GL_FOG_MODE, GL_LINEAR,
          GL_FOG_START, GL_FOG_END, GL_FOG_COLOR, GL_COLOR_BUFFER_BIT, GLfloat)

from pytouhou.utils.maths cimport setup_camera


cdef class GameRenderer(Renderer):
    def __init__(self, resource_loader):
        Renderer.__init__(self, resource_loader)


    def render(self):
        cdef float x, y, z, dx, dy, dz, fog_data[4], fog_start, fog_end
        cdef unsigned char fog_r, fog_g, fog_b
        cdef Matrix mvp

        back = self.background
        game = self.game

        if self.use_fixed_pipeline:
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()

        if game is not None and game.spellcard_effect is not None:
            if self.use_fixed_pipeline:
                glMatrixMode(GL_MODELVIEW)
                glLoadMatrixf(self.game_mvp.data)
                glDisable(GL_FOG)
            else:
                self.game_shader.bind()
                self.game_shader.uniform_matrix('mvp', self.game_mvp)

            self.render_elements([game.spellcard_effect])
        elif back is not None:
            x, y, z = back.position_interpolator.values
            dx, dy, dz = back.position2_interpolator.values
            fog_b, fog_g, fog_r, fog_start, fog_end = back.fog_interpolator.values

            # Those two lines may come from the difference between Direct3D and
            # OpenGL’s distance handling.  The first one seem to calculate fog
            # from the eye, while the second does that starting from the near
            # plane.
            #TODO: investigate, and use a variable to keep the near plane
            # distance at a single place.
            fog_start -= 101010101./2010101.
            fog_end -= 101010101./2010101.

            model = Matrix()
            model.data[12] = -x
            model.data[13] = -y
            model.data[14] = -z
            view = setup_camera(dx, dy, dz)
            mvp = model * view * self.proj

            if self.use_fixed_pipeline:
                glMatrixMode(GL_MODELVIEW)
                glLoadMatrixf(mvp.data)

                glEnable(GL_FOG)
                glFogi(GL_FOG_MODE, GL_LINEAR)
                glFogf(GL_FOG_START, fog_start)
                glFogf(GL_FOG_END,  fog_end)

                fog_data[0] = fog_r / 255.
                fog_data[1] = fog_g / 255.
                fog_data[2] = fog_b / 255.
                fog_data[3] = 1.
                glFogfv(GL_FOG_COLOR, fog_data)
            else:
                self.background_shader.bind()
                self.background_shader.uniform_matrix('mvp', mvp)

                self.background_shader.uniform_1('fog_scale', 1. / (fog_end - fog_start))
                self.background_shader.uniform_1('fog_end', fog_end)
                self.background_shader.uniform_4('fog_color', fog_r / 255., fog_g / 255., fog_b / 255., 1.)

            self.background_renderer.render_background()
        else:
            glClear(GL_COLOR_BUFFER_BIT)

        if game is not None:
            if self.use_fixed_pipeline:
                glMatrixMode(GL_MODELVIEW)
                glLoadMatrixf(self.game_mvp.data)
                glDisable(GL_FOG)
            else:
                self.game_shader.bind()
                self.game_shader.uniform_matrix('mvp', self.game_mvp)

            self.render_elements(enemy for enemy in game.enemies if enemy.visible)
            self.render_elements(game.effects)
            self.render_elements(chain(game.players_bullets,
                                       game.lasers_sprites(),
                                       game.players,
                                       game.msg_sprites()))
            self.render_elements(chain(game.bullets, game.lasers,
                                       game.cancelled_bullets, game.items,
                                       game.labels))
