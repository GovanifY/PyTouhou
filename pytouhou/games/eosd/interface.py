# -*- encoding: utf-8 -*-
##
## Copyright (C) 2014 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from pytouhou.game.effect import Effect
from pytouhou.game.text import Text, Counter, Gauge, NativeText


class Interface:
    width = 640
    height = 480
    game_pos = (32, 16)

    def __init__(self, resource_loader, player_state):
        self.game = None
        self.player_state = player_state
        front = resource_loader.get_single_anm('front.anm')
        self.ascii_anm = resource_loader.get_single_anm('ascii.anm')

        self.highscore = 1000000 #TODO: read score.dat
        self.items = ([Effect((0, 32 * i), 6, front) for i in range(15)] +
                      [Effect((416 + 32 * i, 32 * j), 6, front) for i in range(7) for j in range(15)] +
                      [Effect((32 + 32 * i, 0), 7, front) for i in range(12)] +
                      [Effect((32 + 32 * i, 464), 8, front) for i in range(12)] +
                      [Effect((0, 0), i, front) for i in reversed(range(6))] +
                      [Effect((0, 0), i, front) for i in range(9, 16)])
        for item in self.items:
            item.sprite.allow_dest_offset = True #XXX

        self.level_start = []

        self.labels = {
            'highscore': Text((500, 58), self.ascii_anm, front, text=b'0'),
            'score': Text((500, 82), self.ascii_anm, front, text=b'0'),
            'player': Counter((500, 122), front, front, script=16, value=0),
            'bombs': Counter((500, 146), front, front, script=17, value=0),
            'power': Text((500, 186), self.ascii_anm, front, text=b'0'),
            'graze': Text((500, 206), self.ascii_anm, front, text=b'0'),
            'points': Text((500, 226), self.ascii_anm, front, text=b'0'),
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
            text = ('STAGE %d' % stage).encode()
        elif stage == 6:
            text = b'FINAL STAGE'
        elif stage == 7:
            text = b'EXTRA STAGE'

        self.stage_name = NativeText((192, 200), game.std.name, shadow=True, align='center')
        self.stage_name.set_timeout(240, effect='fadeout', duration=60, start=120)

        self.set_song_name(game.std.bgms[0][0])

        self.level_start = [Text((16+384/2, 200), self.ascii_anm, text=text, align='center')] #TODO: find the exact location.
        self.level_start[0].set_timeout(240, effect='fadeout', duration=60, start=120)
        self.level_start[0].set_color('yellow')


    def set_song_name(self, name):
        #TODO: use the correct animation.
        self.song_name = NativeText((384, 432), '♪ ' + name, shadow=True, align='right')
        self.song_name.set_timeout(240, effect='fadeout', duration=60, start=120)


    def set_boss_life(self):
        if not self.game.boss:
            return
        self.boss_items[1].maximum = self.game.boss.life or 1
        self.boss_items[2].maximum = self.game.boss.life or 1


    def set_spell_life(self):
        self.boss_items[2].set_value(self.game.boss.low_life_trigger if self.game.boss else 0)


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
            boss = self.game.boss

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
                    self.game.sfx_player.set_volume('timeout.wav', 1.)
                    self.game.sfx_player.play('timeout.wav')
            timeout_label.set_text('%02d' % (timeout if timeout >= 0 else 0))
            timeout_label.changed = True
