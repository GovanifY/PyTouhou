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

from pytouhou.lib.sdl import Rect
from .sprite import get_sprite_rendering_data

from pytouhou.utils.helpers import get_logger
logger = get_logger(__name__)


class GameRenderer(object):
    def __init__(self, resource_loader, window):
        self.window = window
        self.texture_manager = TextureManager(resource_loader, self.window.win)


    def load_textures(self, anms):
        self.texture_manager.load(anms)


    def load_background(self, background):
        if background is not None:
            logger.error('Background rendering unavailable in the SDL backend.')


    def start(self, common):
        pass


    def render(self, game):
        self.render_game(game)
        self.render_text(game.texts)
        self.render_interface(game.interface, game.boss)


    def render_game(self, game):
        x, y = game.interface.game_pos
        self.window.win.render_set_viewport(Rect(x, y, game.width, game.height))
        self.window.win.render_set_clip_rect(Rect(x, -y, game.width, game.height))

        if game is not None:
            if game.spellcard_effect is not None:
                self.render_elements([game.spellcard_effect])
            else:
                self.window.win.render_clear()

            self.render_elements([enemy for enemy in game.enemies if enemy.visible])
            self.render_elements(game.effects)
            self.render_elements(chain(game.players_bullets,
                                       game.lasers_sprites(),
                                       game.players,
                                       game.msg_sprites()))
            self.render_elements(chain(game.bullets, game.lasers,
                                       game.cancelled_bullets, game.items,
                                       game.labels))


    def render_interface(self, interface, boss):
        interface.labels['framerate'].set_text('%.2ffps' % self.window.clock.get_fps())

        self.window.win.render_set_viewport(Rect(0, 0, interface.width, interface.height))
        self.window.win.render_set_clip_rect(Rect(0, 0, interface.width, interface.height))

        items = [item for item in interface.items if item.anmrunner and item.anmrunner.running]
        labels = interface.labels.values()

        if items:
            # Redraw all the interface
            self.render_elements(items)
        else:
            # Redraw only changed labels
            labels = [label for label in labels if label.changed]

        self.render_elements(interface.level_start)

        if boss:
            self.render_elements(interface.boss_items)

        self.render_elements(labels)
        for label in labels:
            label.changed = False


    def render_elements(self, elements):
        nb_vertices = 0

        objects = chain(*[element.objects for element in elements])
        for element in objects:
            if nb_vertices >= MAX_ELEMENTS - 4:
                break

            sprite = element.sprite
            if sprite and sprite.visible:
                ox, oy = element.x, element.y
                blendfunc, (vertices, uvs, colors, rotation, flip) = get_sprite_rendering_data(sprite)

                # Pack data in buffer
                x, y, width, height = vertices
                left, right, bottom, top = uvs
                r, g, b, a = colors #TODO: use it.

                #XXX
                texture_width = 256
                texture_height = 256

                source = Rect(left * texture_width, bottom * texture_height, (right - left) * texture_width, (top - bottom) * texture_height)
                dest = Rect(ox + x, oy + y, width, height)

                texture = sprite.anm.texture
                texture.set_color_mod(r, g, b)
                texture.set_alpha_mod(a)
                texture.set_blend_mode(2 if blendfunc else 1)

                if rotation or flip:
                    self.window.win.render_copy_ex(texture, source, dest, rotation, flip)
                else:
                    self.window.win.render_copy(texture, source, dest)

                nb_vertices += 4


    def render_text(self, texts):
        pass
