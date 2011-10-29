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


from pytouhou.game.game import Game
from pytouhou.game.bullettype import BulletType
from pytouhou.game.itemtype import ItemType
from pytouhou.game.player import Player
from pytouhou.game.bullet import Bullet

from math import pi


class EoSDGame(Game):
    def __init__(self, resource_loader, player_states, stage, rank, difficulty, **kwargs):
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
        #TODO: hitbox
        item_types = [ItemType(etama3, 0, 7,  hitbox_size=42, score=10), #Power
                      ItemType(etama3, 1, 8,  hitbox_size=42, score=100000), #Point, TODO: changes for hard, lunatic and poc
                      ItemType(etama3, 2, 9,  hitbox_size=42, score=10), #Big power
                      ItemType(etama3, 3, 10, hitbox_size=42), #Bomb
                      ItemType(etama3, 4, 11, hitbox_size=42, score=1000), #Full power
                      ItemType(etama3, 5, 12, hitbox_size=42), #1up
                      ItemType(etama3, 6, 13, hitbox_size=42, score=500)] #Star

        eosd_characters = [ReimuA, ReimuB, MarisaA, MarisaB]
        players = []
        for player in player_states:
            players.append(eosd_characters[player.character](player, self, resource_loader))

        Game.__init__(self, resource_loader, players, stage, rank, difficulty,
                      bullet_types, item_types, nb_bullets_max=640, **kwargs)


class Reimu(Player):
    def __init__(self, state, game, resource_loader):
        anm_wrapper = resource_loader.get_anm_wrapper(('player00.anm',))
        self.bullet_angle = pi/30 #TODO: check

        Player.__init__(self, state, game, anm_wrapper, speed=4.)


    def fire(self):
        if self.fire_time % self.bullet_launch_interval == 0:
            if self.state.power < 16:
                bullets_per_shot = 1
            elif self.state.power < 48:
                bullets_per_shot = 2
            elif self.state.power < 96:
                bullets_per_shot = 3
            elif self.state.power < 128:
                bullets_per_shot = 4
            elif self.state.power >= 128:
                bullets_per_shot = 5

            bullets = self._game.players_bullets
            nb_bullets_max = self._game.nb_bullets_max

            bullet_angle = self.bullet_launch_angle - self.bullet_angle * (bullets_per_shot - 1) / 2.
            for bullet_nb in range(bullets_per_shot):
                if nb_bullets_max is not None and len(bullets) == nb_bullets_max:
                    break

                bullets.append(Bullet((self.x, self.y), self.bullet_type, 0,
                                      bullet_angle, self.bullet_speed,
                                      (0, 0, 0, 0, 0., 0., 0., 0.),
                                      0, self, self._game, player_bullet=True))
                bullet_angle += self.bullet_angle


class ReimuA(Reimu):
    def __init__(self, state, game, resource_loader):
        Reimu.__init__(self, state, game, resource_loader)

        self.bulletA_type = BulletType(self.anm_wrapper, 65, 97, 0, 0, 0, hitbox_size=4, damage=48) #TODO: verify the hitbox and damages.
        self.bulletA_speed = 12.


    def fire(self):
        Reimu.fire(self)

        if self.state.power < 8:
            return

        else:
            pass #TODO


class ReimuB(Reimu):
    def __init__(self, state, game, resource_loader):
        Reimu.__init__(self, state, game, resource_loader)

        self.bulletB_type = BulletType(self.anm_wrapper, 66, 98, 0, 0, 0, hitbox_size=4, damage=48) #TODO: verify the hitbox and damages.
        self.bulletB_speed = 22.


    def fire_spine(self, offset_x):
        bullets = self._game.players_bullets
        nb_bullets_max = self._game.nb_bullets_max

        if nb_bullets_max is not None and len(bullets) == nb_bullets_max:
            return

        bullets.append(Bullet((self.x + offset_x, self.y), self.bulletB_type, 0,
                              self.bullet_launch_angle, self.bulletB_speed,
                              (0, 0, 0, 0, 0., 0., 0., 0.),
                              0, self, self._game, player_bullet=True))


    def fire(self):
        Reimu.fire(self)

        if self.state.power < 8:
            return

        elif self.state.power < 16:
            if self.fire_time % 15 == 0:
                for offset in (-24, 24):
                    self.fire_spine(offset)

        elif self.state.power < 32:
            if self.fire_time % 10 == 0:
                for offset in (-24, 24):
                    self.fire_spine(offset)

        elif self.state.power < 48:
            if self.fire_time % 8 == 0:
                for offset in (-24, 24):
                    self.fire_spine(offset)

        elif self.state.power < 96:
            if self.fire_time % 5 == 0:
                for offset in (-16, 32):
                    self.fire_spine(offset)
            if self.fire_time % 8 == 0:
                for offset in (-32, 16):
                    self.fire_spine(offset)

        elif self.state.power < 128:
            if self.fire_time % 3 == 0:
                for offset in (-12, 36):
                    self.fire_spine(offset)
            if self.fire_time % 5 == 0:
                for offset in (-36, 12):
                    self.fire_spine(offset)
            if self.fire_time % 10 == 0:
                for offset in (-24, 24):
                    self.fire_spine(offset)

        else:
            if self.fire_time % 3 == 0:
                for offset in (-36, -12, 12, 36):
                    self.fire_spine(offset)
            if self.fire_time % 5 == 0:
                for offset in (-24, 24):
                    self.fire_spine(offset)


class Marisa(Player):
    def __init__(self, state, game, resource_loader):
        anm_wrapper = resource_loader.get_anm_wrapper(('player01.anm',))
        self.bullet_angle = pi/40 #TODO: check

        Player.__init__(self, state, game, anm_wrapper, speed=5.)


    def fire(self):
        if self.fire_time % self.bullet_launch_interval == 0:
            if self.state.power < 32:
                bullets_per_shot = 1
            elif self.state.power < 96:
                bullets_per_shot = 2
            elif self.state.power < 128:
                bullets_per_shot = 3
            elif self.state.power >= 128:
                bullets_per_shot = 5

            bullets = self._game.players_bullets
            nb_bullets_max = self._game.nb_bullets_max

            bullet_angle = self.bullet_launch_angle - self.bullet_angle * (bullets_per_shot - 1) / 2.
            for bullet_nb in range(bullets_per_shot):
                if nb_bullets_max is not None and len(bullets) == nb_bullets_max:
                    break

                bullets.append(Bullet((self.x, self.y), self.bullet_type, 0,
                                      bullet_angle, self.bullet_speed,
                                      (0, 0, 0, 0, 0., 0., 0., 0.),
                                      0, self, self._game, player_bullet=True))
                bullet_angle += self.bullet_angle


class MarisaA(Marisa):
    def __init__(self, state, game, resource_loader):
        Marisa.__init__(self, state, game, resource_loader)

        #TODO: verify the hitbox and damages.
        self.bulletA_types = [BulletType(self.anm_wrapper, 65, 0, 0, 0, 0, hitbox_size=4, damage=48),
                              BulletType(self.anm_wrapper, 66, 0, 0, 0, 0, hitbox_size=4, damage=48),
                              BulletType(self.anm_wrapper, 67, 0, 0, 0, 0, hitbox_size=4, damage=48),
                              BulletType(self.anm_wrapper, 68, 0, 0, 0, 0, hitbox_size=4, damage=48)]
        self.bulletA_speed_interpolator = None


    def fire(self):
        Marisa.fire(self)

        if self.state.power < 8:
            return

        else:
            pass #TODO


class MarisaB(Marisa):
    def __init__(self, state, game, resource_loader):
        Marisa.__init__(self, state, game, resource_loader)

        self.laser_type = None


    def fire(self):
        Marisa.fire(self)

        if self.state.power < 8:
            return

        else:
            pass #TODO
