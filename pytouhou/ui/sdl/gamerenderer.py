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
from os.path import join

from pytouhou.lib.sdl import Rect, SDLError

from pytouhou.utils.helpers import get_logger
logger = get_logger(__name__)


class GameRenderer:
    def __init__(self, resource_loader, window):
        self.window = window
        self.texture_manager = TextureManager(resource_loader, self.window.win)
        font_name = join(resource_loader.game_dir, 'font.ttf')
        try:
            self.font_manager = FontManager(font_name, 16, self.window.win)
        except SDLError:
            self.font_manager = None
            logger.error('Font file “%s” not found, disabling text rendering altogether.', font_name)


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
        interface_labels = interface.labels
        if 'framerate' in interface_labels:
            interface_labels['framerate'].set_text('%.2ffps' % self.window.get_fps())

        self.window.win.render_set_viewport(Rect(0, 0, interface.width, interface.height))
        self.window.win.render_set_clip_rect(Rect(0, 0, interface.width, interface.height))

        items = [item for item in interface.items if item.anmrunner and item.anmrunner.running]
        labels = interface_labels.values()

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
                data = get_sprite_rendering_data(sprite)

                #XXX
                texture_width = 256
                texture_height = 256

                source = Rect(data.left * texture_width,
                              data.bottom * texture_height,
                              (data.right - data.left) * texture_width,
                              (data.top - data.bottom) * texture_height)

                dest = Rect(ox + data.x, oy + data.y, data.width, data.height)

                texture = sprite.anm.texture
                texture.set_color_mod(data.r, data.g, data.b)
                texture.set_alpha_mod(data.a)
                texture.set_blend_mode(2 if data.blendfunc else 1)

                if data.rotation or data.flip:
                    self.window.win.render_copy_ex(texture, source, dest, data.rotation, data.flip)
                else:
                    self.window.win.render_copy(texture, source, dest)

                nb_vertices += 4


    def render_text(self, texts):
        if self.font_manager is None:
            return False

        self.font_manager.load(texts)

        for label in texts.values():
            texture = label.texture

            source = Rect(0, 0, label.width, label.height)
            rect = Rect(label.x, label.y, label.width, label.height)

            texture.set_alpha_mod(label.alpha)

            if label.shadow:
                shadow_rect = Rect(label.x + 1, label.y + 1, label.width, label.height)
                texture.set_color_mod(0, 0, 0)
                self.window.win.render_copy(label.texture, source, shadow_rect)
                texture.set_color_mod(192, 192, 255)
                self.window.win.render_copy(label.texture, source, rect)
            else:
                texture.set_color_mod(192, 192, 255)
                self.window.win.render_copy(label.texture, source, rect)
