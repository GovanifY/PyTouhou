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
          glEnable, glFogi, glFogf, glFogfv, GL_PROJECTION, GL_MODELVIEW,
          GL_FOG, GL_FOG_MODE, GL_LINEAR, GL_FOG_START, GL_FOG_END,
          GL_FOG_COLOR, GL_COLOR_BUFFER_BIT, GLfloat, glViewport, glScissor,
          GL_SCISSOR_TEST, GL_DEPTH_BUFFER_BIT)

from pytouhou.utils.maths cimport perspective, setup_camera, ortho_2d
from pytouhou.game.text cimport NativeText, GlyphCollection
from .shaders.eosd import GameShader, BackgroundShader, PassthroughShader

from collections import namedtuple
Rect = namedtuple('Rect', 'x y w h')
Color = namedtuple('Color', 'r g b a')


cdef class GameRenderer(Renderer):
    def __init__(self, resource_loader, use_fixed_pipeline):
        self.use_fixed_pipeline = use_fixed_pipeline #XXX

        Renderer.__init__(self, resource_loader)

        if not self.use_fixed_pipeline:
            self.game_shader = GameShader()
            self.background_shader = BackgroundShader()
            self.interface_shader = self.game_shader
            self.passthrough_shader = PassthroughShader()

            self.framebuffer = Framebuffer(0, 0, 640, 480)


    cdef void load_background(self, background):
        if background is not None:
            self.background_renderer = BackgroundRenderer(self.use_fixed_pipeline)
            self.background_renderer.load(background)
        else:
            self.background_renderer = None


    cdef void start(self, Game game):
        self.proj = perspective(30, float(game.width) / float(game.height),
                                101010101./2010101., 101010101./10101.)
        game_view = setup_camera(0, 0, 1)
        self.game_mvp = game_view * self.proj
        self.interface_mvp = ortho_2d(0., float(game.interface.width), float(game.interface.height), 0.)


    cdef void render(self, Game game, Window window):
        if not self.use_fixed_pipeline:
            self.framebuffer.bind()

        self.render_game(game)
        self.render_text(game.texts + game.native_texts)
        self.render_interface(game.interface, game.boss)

        if not self.use_fixed_pipeline:
            self.passthrough_shader.bind()
            self.passthrough_shader.uniform_matrix('mvp', self.interface_mvp)
            self.render_framebuffer(self.framebuffer, window)


    cdef void render_game(self, Game game):
        cdef long game_x, game_y
        cdef float x, y, z, dx, dy, dz, fog_data[4], fog_start, fog_end
        cdef unsigned char fog_r, fog_g, fog_b
        cdef Matrix mvp

        game_x, game_y = game.interface.game_pos
        glViewport(game_x, game_y, game.width, game.height)
        glClear(GL_DEPTH_BUFFER_BIT)
        glScissor(game_x, game_y, game.width, game.height)
        glEnable(GL_SCISSOR_TEST)

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
        elif self.background_renderer is not None:
            back = self.background_renderer.background
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

            self.render_elements([enemy for enemy in game.enemies if enemy.visible])
            self.render_elements(game.effects)
            self.render_elements(chain(game.players_bullets,
                                       game.lasers_sprites(),
                                       game.players,
                                       game.msg_sprites()))
            self.render_elements(chain(game.bullets, game.lasers,
                                       game.cancelled_bullets, game.items,
                                       game.labels))

        if game.msg_runner is not None:
            rect = Rect(48, 368, 288, 48)
            color1 = Color(0, 0, 0, 192)
            color2 = Color(0, 0, 0, 128)
            self.render_quads([rect], [(color1, color1, color2, color2)], 0)

        glDisable(GL_SCISSOR_TEST)


    cdef void render_text(self, texts):
        cdef NativeText label

        if self.font_manager is None:
            return

        labels = [label for label in texts if label is not None]
        self.font_manager.load(labels)

        black = Color(0, 0, 0, 255)

        for label in labels:
            if label is None:
                continue

            rect = Rect(label.x, label.y, label.width, label.height)
            gradient = [Color(*color, a=label.alpha) for color in label.gradient]

            if label.shadow:
                shadow_rect = Rect(label.x + 1, label.y + 1, label.width, label.height)
                shadow = [black._replace(a=label.alpha)] * 4
                self.render_quads([shadow_rect, rect], [shadow, gradient], label.texture)
            else:
                self.render_quads([rect], [gradient], label.texture)


    cdef void render_interface(self, interface, game_boss):
        cdef GlyphCollection label

        elements = []

        if self.use_fixed_pipeline:
            glMatrixMode(GL_MODELVIEW)
            glLoadMatrixf(self.interface_mvp.data)
            glDisable(GL_FOG)
        else:
            self.interface_shader.bind()
            self.interface_shader.uniform_matrix('mvp', self.interface_mvp)
        glViewport(0, 0, interface.width, interface.height)

        items = [item for item in interface.items if item.anmrunner and item.anmrunner.running]
        labels = interface.labels.values()

        if items:
            # Redraw all the interface
            elements.extend(items)
        else:
            # Redraw only changed labels
            labels = [label for label in labels if label.changed]

        elements.extend(interface.level_start)

        if game_boss is not None:
            elements.extend(interface.boss_items)

        elements.extend(labels)
        self.render_elements(elements)
        for label in labels:
            label.changed = False
