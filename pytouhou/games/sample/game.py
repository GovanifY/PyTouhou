# -*- encoding: utf-8 -*-
##
## Copyright (C) 2011 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from pytouhou.utils.interpolator import Interpolator

from pytouhou.game.game import Game as GameBase
from pytouhou.game.bullettype import BulletType
from pytouhou.game.lasertype import LaserType
from pytouhou.game.itemtype import ItemType
from pytouhou.game.player import Player as PlayerBase
from pytouhou.game.orb import Orb
from pytouhou.game.background import Background

from pytouhou.vm import PythonMainRunner
from . import enemies, shots


class Common:
    default_power = [0, 64, 128, 128, 128, 128, 0]

    def __init__(self, resource_loader, player_characters, continues, *,
                 width=384, height=448):
        self.width, self.height = width, height

        self.etama = resource_loader.get_multi_anm(('etama3.anm', 'etama4.anm'))
        self.bullet_types = [BulletType(self.etama[0], 0, 11, 14, 15, 16, hitbox_size=2,
                                        type_id=0),
                             BulletType(self.etama[0], 1, 12, 17, 18, 19, hitbox_size=3,
                                        type_id=1),
                             BulletType(self.etama[0], 2, 12, 17, 18, 19, hitbox_size=2,
                                        type_id=2),
                             BulletType(self.etama[0], 3, 12, 17, 18, 19, hitbox_size=3,
                                        type_id=3),
                             BulletType(self.etama[0], 4, 12, 17, 18, 19, hitbox_size=2.5,
                                        type_id=4),
                             BulletType(self.etama[0], 5, 12, 17, 18, 19, hitbox_size=2,
                                        type_id=5),
                             BulletType(self.etama[0], 6, 13, 20, 20, 20, hitbox_size=8,
                                        launch_anim_offsets=(0, 1, 1, 2, 2, 3, 4, 0),
                                        type_id=6),
                             BulletType(self.etama[0], 7, 13, 20, 20, 20, hitbox_size=5.5,
                                        launch_anim_offsets=(1, 1, 1, 1),
                                        type_id=7),
                             BulletType(self.etama[0], 8, 13, 20, 20, 20, hitbox_size=4.5,
                                        launch_anim_offsets=(0, 1, 1, 2, 2, 3, 4, 0),
                                        type_id=8),
                             BulletType(self.etama[1], 0, 1, 2, 2, 2, hitbox_size=16,
                                        launch_anim_offsets=(0, 1, 2, 3),
                                        type_id=9)]

        self.laser_types = [LaserType(self.etama[0], 9),
                            LaserType(self.etama[0], 10)]

        self.item_types = [ItemType(self.etama[0], 0, 7), #Power
                           ItemType(self.etama[0], 1, 8), #Point
                           ItemType(self.etama[0], 2, 9), #Big power
                           ItemType(self.etama[0], 3, 10), #Bomb
                           ItemType(self.etama[0], 4, 11), #Full power
                           ItemType(self.etama[0], 5, 12), #1up
                           ItemType(self.etama[0], 6, 13)] #Star

        self.enemy_face = [('face03a.anm', 'face03b.anm'),
                           ('face05a.anm',),
                           ('face06a.anm', 'face06b.anm'),
                           ('face08a.anm', 'face08b.anm'),
                           ('face09a.anm', 'face09b.anm'),
                           ('face09b.anm', 'face10a.anm', 'face10b.anm'),
                           ('face08a.anm', 'face12a.anm', 'face12b.anm', 'face12c.anm')]

        sample_characters = shots.characters
        self.first_character = player_characters[0] // 2
        self.player_anms = {}
        self.players = [None] * len(player_characters)
        for i, player_character in enumerate(player_characters):
            character = player_character // 2
            if character not in self.player_anms:
                face = resource_loader.get_multi_anm(('face0%da.anm' % character,
                                                      'face0%db.anm' % character,
                                                      'face0%dc.anm' % character))
                anm = resource_loader.get_single_anm('player0%d.anm' % character)
                self.player_anms[character] = (anm, face)

            self.players[i] = Player(i, self.player_anms[character][0],
                                     sample_characters[player_character],
                                     character, continues)



class Game(GameBase):
    def __init__(self, resource_loader, stage, rank, difficulty,
                 common, prng, hints=None, friendly_fire=True,
                 nb_bullets_max=640):

        self.etama = common.etama #XXX
        try:
            self.enm_anm = resource_loader.get_multi_anm(('stg%denm.anm' % stage,
                                                          'stg%denm2.anm' % stage))
        except KeyError:
            self.enm_anm = resource_loader.get_anm('stg%denm.anm' % stage)

        self.ecl_runners = [PythonMainRunner(getattr(enemies, 'stage%d' % stage), self)]

        self.spellcard_effect_anm = resource_loader.get_single_anm('eff0%d.anm' % stage)

        self.msg = resource_loader.get_msg('msg%d.dat' % stage)
        msg_anm = [common.player_anms[common.first_character][1], #TODO: does it break bomb face of non-first player?
                   resource_loader.get_multi_anm(common.enemy_face[stage - 1])]

        self.msg_anm = [[], []]
        for i, anms in enumerate(msg_anm):
            for anm in anms:
                for sprite in anm.sprites.values():
                    self.msg_anm[i].append((anm, sprite))

        for player in common.players:
            player._game = self
            if player.power < 0:
                player.power = common.default_power[stage - 1]

        # Load stage data
        self.std = resource_loader.get_stage('stage%d.std' % stage)

        background_anm = resource_loader.get_single_anm('stg%dbg.anm' % stage)
        self.background = Background(self.std, background_anm)

        common.interface.start_stage(self, stage)

        GameBase.__init__(self, common.players, stage, rank, difficulty,
                          common.bullet_types, common.laser_types,
                          common.item_types, nb_bullets_max, common.width,
                          common.height, prng, common.interface, hints,
                          friendly_fire)



class Player(PlayerBase):
    def __init__(self, number, anm, shts, character, continues):
        self.sht = shts[0]
        self.focused_sht = shts[1]

        PlayerBase.__init__(self, number, anm, character, continues, power=-1)

        self.orbs = [Orb(anm, 128, self),
                     Orb(anm, 129, self)]

        self.orbs[0].offset_x = -24
        self.orbs[1].offset_x = 24

    def start_focusing(self):
        self.focused = True

    def stop_focusing(self):
        self.focused = False

    @property
    def objects(self):
        return [self] + self.orbs

    def update(self, keystate):
        PlayerBase.update(self, keystate)

        for orb in self.orbs:
            orb.update()
