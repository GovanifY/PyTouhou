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
from pytouhou.game.text import Text, Counter, Gauge, NativeText
from pytouhou.game.background import Background

from pytouhou.vm.eclrunner import ECLMainRunner


class EoSDCommon(object):
    def __init__(self, resource_loader, player_state):
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

        self.characters = resource_loader.get_eosd_characters()
        self.interface = EoSDInterface(resource_loader, player_state)



class EoSDGame(Game):
    def __init__(self, resource_loader, player_states, stage, rank, difficulty,
                 common, nb_bullets_max=640, width=384, height=448, prng=None,
                 hints=None):

        self.etama = common.etama #XXX
        try:
            self.enm_anm = resource_loader.get_multi_anm(('stg%denm.anm' % stage,
                                                          'stg%denm2.anm' % stage))
        except KeyError:
            self.enm_anm = resource_loader.get_anm('stg%denm.anm' % stage)
        ecl = resource_loader.get_ecl('ecldata%d.ecl' % stage)
        self.ecl_runners = [ECLMainRunner(main, ecl.subs, self) for main in ecl.mains]

        self.spellcard_effect_anm = resource_loader.get_single_anm('eff0%d.anm' % stage)

        player_face = player_states[0].character // 2
        self.msg = resource_loader.get_msg('msg%d.dat' % stage)
        msg_anm = [resource_loader.get_multi_anm(('face0%da.anm' % player_face,
                                                  'face0%db.anm' % player_face,
                                                  'face0%dc.anm' % player_face)),
                   resource_loader.get_multi_anm(common.enemy_face[stage - 1])]

        self.msg_anm = [[], []]
        for i, anms in enumerate(msg_anm):
            for anm in anms:
                for sprite in anm.sprites.values():
                    self.msg_anm[i].append((anm, sprite))

        players = [EoSDPlayer(state, self, resource_loader, common.characters[state.character]) for state in player_states]

        # Load stage data
        self.std = resource_loader.get_stage('stage%d.std' % stage)

        background_anm = resource_loader.get_single_anm('stg%dbg.anm' % stage)
        self.background = Background(self.std, background_anm)

        common.interface.start_stage(self, stage)
        self.native_texts = [common.interface.stage_name, common.interface.song_name]

        self.resource_loader = resource_loader #XXX: currently used for texture preload in pytouhou.ui.gamerunner. Wipe it!

        Game.__init__(self, players, stage, rank, difficulty,
                      common.bullet_types, common.laser_types,
                      common.item_types, nb_bullets_max, width, height, prng,
                      common.interface, hints)



class EoSDInterface(object):
    def __init__(self, resource_loader, player_state):
        self.game = None
        self.player_state = player_state
        front = resource_loader.get_single_anm('front.anm')
        self.ascii_anm = resource_loader.get_single_anm('ascii.anm')

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

        self.level_start = []

        self.labels = {
            'highscore': Text((500, 58), self.ascii_anm, front, text='0'),
            'score': Text((500, 82), self.ascii_anm, front, text='0'),
            'player': Counter((500, 122), front, front, script=16, value=0),
            'bombs': Counter((500, 146), front, front, script=17, value=0),
            'power': Text((500, 186), self.ascii_anm, front, text='0'),
            'graze': Text((500, 206), self.ascii_anm, front, text='0'),
            'points': Text((500, 226), self.ascii_anm, front, text='0'),
            'framerate': Text((512, 464), self.ascii_anm, front),
            'debug?': Text((0, 464), self.ascii_anm, front),

            # Only when there is a boss.
            'boss_lives': Text((80, 16), self.ascii_anm),
            'timeout': Text((384, 16), self.ascii_anm),
        }
        self.labels['boss_lives'].set_color('yellow')

        self.boss_items = [
            Effect((0, 0), 19, front), # Enemy
            Gauge((100, 24), front), # Gauge
            Gauge((100, 24), front), # Spellcard gauge
        ]
        for item in self.boss_items:
            item.sprite.allow_dest_offset = True #XXX


    def start_stage(self, game, stage):
        self.game = game
        if stage < 6:
            text = 'STAGE %d' % stage
        elif stage == 6:
            text = 'FINAL STAGE'
        elif stage == 7:
            text = 'EXTRA STAGE'

        self.stage_name = NativeText((192, 200), unicode(game.std.name), shadow=True, align='center')
        self.stage_name.set_timeout(240, effect='fadeout', duration=60, start=120)

        self.set_song_name(game.std.bgms[0][0])

        self.level_start = [Text((16+384/2, 200), self.ascii_anm, text=text, align='center')] #TODO: find the exact location.
        self.level_start[0].set_timeout(240, effect='fadeout', duration=60, start=120)
        self.level_start[0].set_color('yellow')


    def set_song_name(self, name):
        #TODO: use the correct animation.
        self.song_name = NativeText((384, 432), u'♪ ' + name, shadow=True, align='right')
        self.song_name.set_timeout(240, effect='fadeout', duration=60, start=120)


    def set_boss_life(self):
        if not self.game.boss:
            return
        self.boss_items[1].maximum = self.game.boss._enemy.life or 1
        self.boss_items[2].maximum = self.game.boss._enemy.life or 1


    def set_spell_life(self):
        self.boss_items[2].set_value(self.game.boss._enemy.low_life_trigger if self.game.boss else 0)


    def update(self):
        for elem in self.items:
            elem.update()

        for elem in self.level_start:
            elem.update()
            if elem.removed: #XXX
                self.level_start = []

        player_state = self.player_state

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

            timeout = min((boss.timeout - boss.frame) // 60, 99)
            timeout_label = self.labels['timeout']
            if timeout >= 20:
                timeout_label.set_color('blue')
            elif timeout >= 10:
                timeout_label.set_color('darkblue')
            else:
                if timeout >= 5:
                    timeout_label.set_color('purple')
                else:
                    timeout_label.set_color('red')
                if (boss.timeout - boss.frame) % 60 == 0 and boss.timeout != 0:
                    self.game.sfx_player.play('timeout.wav', volume=1.)
            timeout_label.set_text('%02d' % (timeout if timeout >= 0 else 0))
            timeout_label.changed = True



class EoSDPlayer(Player):
    def __init__(self, state, game, resource_loader, character):
        self.sht = character[0]
        self.focused_sht = character[1]
        self.anm = resource_loader.get_single_anm('player0%d.anm' % (state.character // 2))

        Player.__init__(self, state, game, self.anm)

        self.orbs = [Orb(self.anm, 128, self.state),
                     Orb(self.anm, 129, self.state)]

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


    @property
    def objects(self):
        return [self] + (self.orbs if self.state.power >= 8 else [])


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
