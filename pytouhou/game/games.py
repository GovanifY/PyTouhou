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

from pytouhou.game.game import Game
from pytouhou.game.character import Character
from pytouhou.game.bullettype import BulletType

class EoSDGame(Game):
    def __init__(self, resource_loader, players, stage, rank, difficulty):
        etama3 = resource_loader.get_anm_wrapper(('etama3.anm',))
        etama4 = resource_loader.get_anm_wrapper(('etama4.anm',))
        bullet_types = [BulletType(etama3, 0, 11, 14, 15, 16, hitbox_size=4),
                        BulletType(etama3, 1, 12, 17, 18, 19, hitbox_size=6),
                        BulletType(etama3, 2, 12, 17, 18, 19, hitbox_size=4),
                        BulletType(etama3, 3, 12, 17, 18, 19, hitbox_size=6),
                        BulletType(etama3, 4, 12, 17, 18, 19, hitbox_size=5),
                        BulletType(etama3, 5, 12, 17, 18, 19, hitbox_size=4),
                        BulletType(etama3, 6, 13, 20, 20, 20, hitbox_size=16),
                        BulletType(etama3, 7, 13, 20, 20, 20, hitbox_size=11),
                        BulletType(etama3, 8, 13, 20, 20, 20, hitbox_size=9),
                        BulletType(etama4, 0, 1, 2, 2, 2, hitbox_size=32)]

        player00 = resource_loader.get_anm_wrapper(('player00.anm',))
        player01 = resource_loader.get_anm_wrapper(('player01.anm',))
        characters = [Character(player00, 4., 2., 2.5),
                      Character(player00, 4., 2., 2.5),
                      Character(player01, 5., 2.5, 2.5),
                      Character(player01, 5., 2.5, 2.5)]

        Game.__init__(self, resource_loader, players, stage, rank, difficulty,
                      bullet_types, characters)

