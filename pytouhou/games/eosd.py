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

from pytouhou.game.game import Game
from pytouhou.game.bullettype import BulletType
from pytouhou.game.lasertype import LaserType
from pytouhou.game.itemtype import ItemType
from pytouhou.game.player import Player
from pytouhou.game.orb import Orb
from pytouhou.game.effect import Effect
from pytouhou.game.text import Text, Counter, Gauge


SQ2 = 2. ** 0.5 / 2.


class EoSDGame(Game):
    def __init__(self, resource_loader, player_states, stage, rank, difficulty,
                 bullet_types=None, laser_types=None, item_types=None,
                 nb_bullets_max=640, width=384, height=448, prng=None, continues=0):

        if not bullet_types:
            etama3 = resource_loader.get_anm_wrapper(('etama3.anm',))
            etama4 = resource_loader.get_anm_wrapper(('etama4.anm',))
            bullet_types = [BulletType(etama3, 0, 11, 14, 15, 16, hitbox_size=4,
                                       type_id=0),
                            BulletType(etama3, 1, 12, 17, 18, 19, hitbox_size=6,
                                       type_id=1),
                            BulletType(etama3, 2, 12, 17, 18, 19, hitbox_size=4,
                                       type_id=2),
                            BulletType(etama3, 3, 12, 17, 18, 19, hitbox_size=6,
                                       type_id=3),
                            BulletType(etama3, 4, 12, 17, 18, 19, hitbox_size=5,
                                       type_id=4),
                            BulletType(etama3, 5, 12, 17, 18, 19, hitbox_size=4,
                                       type_id=5),
                            BulletType(etama3, 6, 13, 20, 20, 20, hitbox_size=16,
                                       launch_anim_offsets=(0, 1, 1, 2, 2, 3, 4, 0),
                                       type_id=6),
                            BulletType(etama3, 7, 13, 20, 20, 20, hitbox_size=11,
                                       launch_anim_offsets=(1,)*28,
                                       type_id=7),
                            BulletType(etama3, 8, 13, 20, 20, 20, hitbox_size=9,
                                       launch_anim_offsets=(0, 1, 1, 2, 2, 3, 4, 0),
                                       type_id=8),
                            BulletType(etama4, 0, 1, 2, 2, 2, hitbox_size=32,
                                       launch_anim_offsets=(0, 1, 2, 3, 4, 5, 6, 7, 8),
                                       type_id=9)]

        if not laser_types:
            laser_types = [LaserType(etama3, 9),
                           LaserType(etama3, 10)]

        if not item_types:
            item_types = [ItemType(etama3, 0, 7), #Power
                          ItemType(etama3, 1, 8), #Point
                          ItemType(etama3, 2, 9), #Big power
                          ItemType(etama3, 3, 10), #Bomb
                          ItemType(etama3, 4, 11), #Full power
                          ItemType(etama3, 5, 12), #1up
                          ItemType(etama3, 6, 13)] #Star

        player_face = player_states[0].character // 2
        enemy_face = [('face03a.anm', 'face03b.anm'),
                      ('face05a.anm',),
                      ('face06a.anm', 'face06b.anm'),
                      ('face08a.anm', 'face08b.anm'),
                      ('face09a.anm', 'face09b.anm'),
                      ('face09b.anm', 'face10a.anm', 'face10b.anm'),
                      ('face08a.anm', 'face12a.anm', 'face12b.anm', 'face12c.anm')]
        self.msg = resource_loader.get_msg('msg%d.dat' % stage)
        self.msg_anm_wrapper = resource_loader.get_anm_wrapper2(('face0%da.anm' % player_face,
                                                                 'face0%db.anm' % player_face,
                                                                 'face0%dc.anm' % player_face)
                                                                + enemy_face[stage - 1],
                                                                (0, 2, 4, 8, 10, 11, 12))

        characters = resource_loader.get_eosd_characters()
        players = [EoSDPlayer(state, self, resource_loader, characters[state.character]) for state in player_states]

        interface = EoSDInterface(self, resource_loader)

        Game.__init__(self, resource_loader, players, stage, rank, difficulty,
                      bullet_types, laser_types, item_types, nb_bullets_max,
                      width, height, prng, interface, continues)



class EoSDInterface(object):
    def __init__(self, game, resource_loader):
        self.game = game
        front = resource_loader.get_anm_wrapper(('front.anm',))
        ascii_wrapper = resource_loader.get_anm_wrapper(('ascii.anm',))

        self.width = 640
        self.height = 480
        self.game_pos = (32, 16)

        self.highscore = 1000000 #TODO: read score.dat
        self.items = ([Effect((0, 32 * i), 6, front) for i in range(15)] +
                      [Effect((416 + 32 * i, 32 * j), 6, front) for i in range(7) for j in range(15)] +
                      [Effect((32 + 32 * i, 0), 7, front) for i in range(12)] +
                      [Effect((32 + 32 * i, 464), 8, front) for i in range(12)] +
                      [Effect((0, 0), 5, front)] +
                      [Effect((0, 0), i, front) for i in range(5) + range(9, 16)])
        for item in self.items:
            item.sprite.allow_dest_offset = True #XXX

        self.labels = {
            'highscore': Text((500, 58), ascii_wrapper, front, text='0'),
            'score': Text((500, 82), ascii_wrapper, front, text='0'),
            'player': Counter((500, 122), front, front, script=16, value=0),
            'bombs': Counter((500, 146), front, front, script=17, value=0),
            'power': Text((500, 186), ascii_wrapper, front, text='0'),
            'graze': Text((500, 206), ascii_wrapper, front, text='0'),
            'points': Text((500, 226), ascii_wrapper, front, text='0'),
            'framerate': Text((512, 464), ascii_wrapper, front),
            'debug?': Text((0, 464), ascii_wrapper, front),

            # Only when there is a boss.
            'boss_lives': Text((80, 16), ascii_wrapper),
            'timeout': Text((384, 16), ascii_wrapper),
        }
        self.labels['boss_lives'].set_color('yellow')

        self.boss_items = [
            Effect((0, 0), 19, front), # Enemy
            Gauge((100, 24), front), # Gauge
            Gauge((100, 24), front), # Spellcard gauge
        ]
        for item in self.boss_items:
            item.sprite.allow_dest_offset = True #XXX


    def set_boss_life(self):
        self.boss_items[1].maximum = self.game.boss._enemy.life or 1
        self.boss_items[2].maximum = self.game.boss._enemy.life or 1


    def set_spell_life(self):
        self.boss_items[2].set_value(self.game.boss._enemy.low_life_trigger if self.game.boss else 0)


    def update(self):
        for elem in self.items:
            elem.update()

        player_state = self.game.players[0].state

        self.highscore = max(self.highscore, player_state.effective_score)
        self.labels['highscore'].set_text('%09d' % self.highscore)
        self.labels['score'].set_text('%09d' % player_state.effective_score)
        self.labels['power'].set_text('%d' % player_state.power)
        self.labels['graze'].set_text('%d' % player_state.graze)
        self.labels['points'].set_text('%d' % player_state.points)
        self.labels['player'].set_value(player_state.lives)
        self.labels['bombs'].set_value(player_state.bombs)

        if self.game.boss:
            boss = self.game.boss._enemy

            life_gauge = self.boss_items[1]
            life_gauge.set_value(boss.life)

            spell_gauge = self.boss_items[2]
            spell_gauge.sprite.color = (255, 192, 192)
            if boss.life < spell_gauge.value:
                spell_gauge.set_value(boss.life)

            for item in self.boss_items:
                item.update()

            self.labels['boss_lives'].set_text('%d' % boss.remaining_lives)
            self.labels['boss_lives'].changed = True

            timeout = (boss.timeout - boss.frame) // 60
            timeout_label = self.labels['timeout']
            if timeout >= 20:
                timeout_label.set_color('blue')
            elif timeout >= 10:
                timeout_label.set_color('darkblue')
            elif timeout >= 5:
                timeout_label.set_color('purple')
            else:
                timeout_label.set_color('red')
            timeout_label.set_text('%02d' % (timeout if timeout >= 0 else 0))
            timeout_label.changed = True



class EoSDPlayer(Player):
    def __init__(self, state, game, resource_loader, character):
        self.sht = character[0]
        self.focused_sht = character[1]
        anm_wrapper = resource_loader.get_anm_wrapper(('player0%d.anm' % (state.character // 2),))
        self.anm_wrapper = anm_wrapper

        Player.__init__(self, state, game, anm_wrapper)

        self.orbs = [Orb(self.anm_wrapper, 128, self.state, None),
                     Orb(self.anm_wrapper, 129, self.state, None)]

        self.orbs[0].offset_x = -24
        self.orbs[1].offset_x = 24

        self.orb_dx_interpolator = None
        self.orb_dy_interpolator = None


    def start_focusing(self):
        self.orb_dx_interpolator = Interpolator((24,), self._game.frame,
                                                (8,), self._game.frame + 8,
                                                lambda x: x ** 2)
        self.orb_dy_interpolator = Interpolator((0,), self._game.frame,
                                                (-32,), self._game.frame + 8)
        self.state.focused = True


    def stop_focusing(self):
        self.orb_dx_interpolator = Interpolator((8,), self._game.frame,
                                                (24,), self._game.frame + 8,
                                                lambda x: x ** 2)
        self.orb_dy_interpolator = Interpolator((-32,), self._game.frame,
                                                (0,), self._game.frame + 8)
        self.state.focused = False


    def objects(self):
        return self.orbs if self.state.power >= 8 else []


    def update(self, keystate):
        Player.update(self, keystate)

        if self.death_time == 0 or self._game.frame - self.death_time > 60:
            if self.orb_dx_interpolator:
                self.orb_dx_interpolator.update(self._game.frame)
                dx, = self.orb_dx_interpolator.values
                self.orbs[0].offset_x = -dx
                self.orbs[1].offset_x = dx
            if self.orb_dy_interpolator:
                self.orb_dy_interpolator.update(self._game.frame)
                dy, = self.orb_dy_interpolator.values
                self.orbs[0].offset_y = dy
                self.orbs[1].offset_y = dy

        for orb in self.orbs:
            orb.update()

