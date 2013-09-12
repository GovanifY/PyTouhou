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

from libc.math cimport cos, sin, atan2, M_PI as pi


cdef class Indicator(Element):
    def __init__(self, Item item):
        Element.__init__(self)

        self._item = item
        self.sprite = item._item_type.indicator_sprite.copy()

        self.x = self._item.x
        self.y = self.sprite.texcoords[2] / 2.


    cdef void update(self) nogil:
        #TODO: alpha
        self.x = self._item.x



cdef class Item(Element):
    def __init__(self, start_pos, long _type, item_type, Game game, double angle=pi/2, Player player=None, end_pos=None):
        Element.__init__(self, start_pos)

        self._game = game
        self._type = _type
        self._item_type = item_type
        self.sprite = item_type.sprite

        self.frame = 0
        self.angle = angle
        self.indicator = None

        if player is not None:
            self.autocollect(player)
        else:
            self.player = None

            #TODO: find the formulae in the binary.
            self.speed_interpolator = None
            if end_pos:
                self.pos_interpolator = Interpolator(start_pos, 0,
                                                     end_pos, 60)
            else:
                self.speed_interpolator = Interpolator((-2.,), 0,
                                                       (0.,), 60)

        self.sprite.angle = angle


    property objects:
        def __get__(self):
            if self.indicator is not None:
                return [self.indicator]
            return [self]


    cdef void autocollect(self, Player player):
        if self.player is None:
            self.player = player
            self.speed = player.sht.autocollection_speed


    cdef void on_collect(self, Player player):
        cdef long level, poc

        player_state = player.state
        old_power = player_state.power
        score = 0
        label = None
        color = 'white'
        player.play_sound('item00')

        if self._type == 0 or self._type == 2: # power or big power
            if old_power < 128:
                player_state.power_bonus = 0
                score = 10
                player_state.power += (1 if self._type == 0 else 8)
                if player_state.power > 128:
                    player_state.power = 128
                for level in (8, 16, 32, 48, 64, 96):
                    if old_power < level and player_state.power >= level:
                        label = self._game.new_label((self.x, self.y), ':') # Actually a “PowerUp” character.
                        color = 'blue'
                        label.set_color(color)
                        labeled = True
            else:
                bonus = player_state.power_bonus + (1 if self._type == 0 else 8)
                if bonus > 30:
                    bonus = 30
                if bonus < 9:
                    score = (bonus + 1) * 10
                elif bonus < 18:
                    score = (bonus - 8) * 100
                elif bonus < 30:
                    score = (bonus - 17) * 1000
                elif bonus == 30:
                    score = 51200
                    color = 'yellow'
                player_state.power_bonus = bonus
            self._game.modify_difficulty(+1)

        elif self._type == 1: # point
            player_state.points += 1
            poc = player.sht.point_of_collection
            if player_state.y < poc:
                score = 100000
                self._game.modify_difficulty(+30)
                color = 'yellow'
            else:
                #score =  #TODO: find the formula.
                self._game.modify_difficulty(+3)

        elif self._type == 3: # bomb
            if player_state.bombs < 8:
                player_state.bombs += 1
            self._game.modify_difficulty(+5)

        elif self._type == 4: # full power
            score = 1000
            player_state.power = 128

        elif self._type == 5: # 1up
            if player_state.lives < 8:
                player_state.lives += 1
            self._game.modify_difficulty(+200)
            player.play_sound('extend')

        elif self._type == 6: # star
            score = 500

        if old_power < 128 and player_state.power == 128:
            #TODO: display “full power”.
            self._game.change_bullets_into_star_items()

        if score > 0:
            player_state.score += score
            if label is None:
                label = self._game.new_label((self.x, self.y), str(score))
                if color != 'white':
                    label.set_color(color)

        self.removed = True


    cpdef update(self):
        cdef bint offscreen

        if self.frame == 60:
            self.speed_interpolator = Interpolator((0.,), 60,
                                                   (3.,), 180)

        if self.player is not None:
            player_state = self.player.state
            self.angle = atan2(player_state.y - self.y, player_state.x - self.x)
            self.x += cos(self.angle) * self.speed
            self.y += sin(self.angle) * self.speed
        elif self.speed_interpolator is None:
            self.pos_interpolator.update(self.frame)
            self.x, self.y = self.pos_interpolator.values
        else:
            self.speed_interpolator.update(self.frame)
            self.speed, = self.speed_interpolator.values
            dx, dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed
            self.x += dx
            self.y += dy

        offscreen = self.y < -(<double>self.sprite.texcoords[2] / 2.)
        if offscreen:
            if self.indicator is None:
                self.indicator = Indicator(self)
            self.indicator.update()
        else:
            self.indicator = None

        self.frame += 1
