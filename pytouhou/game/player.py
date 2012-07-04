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


from pytouhou.game.sprite import Sprite
from pytouhou.vm.anmrunner import ANMRunner
from pytouhou.game.bullettype import BulletType
from pytouhou.game.bullet import Bullet
from pytouhou.game.lasertype import LaserType
from pytouhou.game.laser import PlayerLaser
from pytouhou.game.game import GameOver

from math import pi


class PlayerState(object):
    def __init__(self, character=0, score=0, power=0, lives=2, bombs=3):
        self.character = character # ReimuA/ReimuB/MarisaA/MarisaB/...

        self.score = score
        self.effective_score = score
        self.lives = lives
        self.bombs = bombs
        self.power = power

        self.graze = 0
        self.points = 0

        self.x = 192.0
        self.y = 384.0

        self.invulnerable_time = 240
        self.touchable = True
        self.focused = False

        self.power_bonus = 0 # Never goes over 30.


    def copy(self):
        return PlayerState(self.character, self.score,
                           self.power, self.lives, self.bombs)


class Player(object):
    def __init__(self, state, game, anm_wrapper):
        self._game = game
        self.sprite = None
        self.anmrunner = None
        self.anm_wrapper = anm_wrapper

        self.speeds = (self.sht.horizontal_vertical_speed,
                       self.sht.diagonal_speed,
                       self.sht.horizontal_vertical_focused_speed,
                       self.sht.diagonal_focused_speed)

        self.hitbox_half_size = self.sht.hitbox / 2.
        self.graze_hitbox_half_size = self.sht.graze_hitbox / 2.

        self.fire_time = 0

        self.state = state
        self.direction = None

        self.set_anim(0)

        self.death_time = 0


    @property
    def x(self):
        return self.state.x


    @property
    def y(self):
        return self.state.y


    def objects(self):
        return []


    def set_anim(self, index):
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(self.anm_wrapper, index, self.sprite)
        self.anmrunner.run_frame()


    def play_sound(self, name):
        self._game.player_sfx.play('%s.wav' % name)


    def collide(self):
        if not self.state.invulnerable_time and not self.death_time and self.state.touchable: # Border Between Life and Death
            self.death_time = self._game.frame
            self._game.new_effect((self.state.x, self.state.y), 17)
            self._game.modify_difficulty(-1600)
            self.play_sound('pldead00')
            for i in range(16):
                self._game.new_particle((self.state.x, self.state.y), 2, 4., 256) #TODO: find the real size and range.


    def start_focusing(self):
        self.state.focused = True


    def stop_focusing(self):
        self.state.focused = False


    def fire(self):
        sht = self.focused_sht if self.state.focused else self.sht
        power = min(power for power in sht.shots if self.state.power < power)

        bullets = self._game.players_bullets
        lasers = self._game.players_lasers
        nb_bullets_max = self._game.nb_bullets_max

        if self.fire_time % 5 == 0:
            self.play_sound('plst00')

        for shot in sht.shots[power]:
            origin = self.orbs[shot.orb - 1] if shot.orb else self.state

            if shot.type == 3:
                if self.fire_time != 30:
                    continue

                number = shot.delay #TODO: number can do very surprising things, like removing any bullet creation from enemies with 3. For now, crash when not 0 or 1.
                if lasers[number]:
                    continue

                laser_type = LaserType(self.anm_wrapper, shot.sprite % 256, 68)
                lasers[number] = PlayerLaser(laser_type, 0, shot.hitbox, shot.damage, shot.angle, shot.speed, shot.interval, origin)
                continue

            if (self.fire_time + shot.delay) % shot.interval != 0:
                continue

            if nb_bullets_max is not None and len(bullets) == nb_bullets_max:
                break

            x = origin.x + shot.pos[0]
            y = origin.y + shot.pos[1]

            #TODO: find a better way to do that.
            bullet_type = BulletType(self.anm_wrapper, shot.sprite % 256,
                                     shot.sprite % 256 + 32, #TODO: find the real cancel anim
                                     0, 0, 0, 0.)
            #TODO: Type 1 (homing bullets)
            if shot.type == 2:
                #TODO: triple-check acceleration!
                bullets.append(Bullet((x, y), bullet_type, 0,
                                      shot.angle, shot.speed,
                                      (-1, 0, 0, 0, 0.15, -pi/2., 0., 0.),
                                      16, self, self._game, player_bullet=True,
                                      damage=shot.damage, hitbox=shot.hitbox))
            else:
                bullets.append(Bullet((x, y), bullet_type, 0,
                                      shot.angle, shot.speed,
                                      (0, 0, 0, 0, 0., 0., 0., 0.),
                                      0, self, self._game, player_bullet=True,
                                      damage=shot.damage, hitbox=shot.hitbox))


    def update(self, keystate):
        if self.death_time == 0 or self._game.frame - self.death_time > 60:
            speed, diag_speed = self.speeds[2:] if self.state.focused else self.speeds[:2]
            try:
                dx, dy = {16: (0.0, -speed), 32: (0.0, speed), 64: (-speed, 0.0), 128: (speed, 0.0),
                          16|64: (-diag_speed, -diag_speed), 16|128: (diag_speed, -diag_speed),
                          32|64: (-diag_speed, diag_speed), 32|128:  (diag_speed, diag_speed)}[keystate & (16|32|64|128)]
            except KeyError:
                dx, dy = 0.0, 0.0

            if dx < 0 and self.direction != -1:
                self.set_anim(1)
                self.direction = -1
            elif dx > 0 and self.direction != +1:
                self.set_anim(3)
                self.direction = +1
            elif dx == 0 and self.direction is not None:
                self.set_anim({-1: 2, +1: 4}[self.direction])
                self.direction = None

            self.state.x += dx
            self.state.y += dy

            if not self.state.focused and keystate & 4:
                self.start_focusing()
            elif self.state.focused and not keystate & 4:
                self.stop_focusing()

            if self.state.invulnerable_time > 0:
                self.state.invulnerable_time -= 1

                m = self.state.invulnerable_time % 8
                if m == 7 or self.state.invulnerable_time == 0:
                    self.sprite.color = (255, 255, 255)
                    self.sprite.changed = True
                elif m == 1:
                    self.sprite.color = (64, 64, 64)
                    self.sprite.changed = True

            if keystate & 1 and self.fire_time == 0:
                self.fire_time = 30
            if self.fire_time > 0:
                self.fire()
                self.fire_time -= 1

        if self.death_time:
            time = self._game.frame - self.death_time
            if time == 6: # too late, you are dead :(
                self.state.touchable = False
                if self.state.power > 16:
                    self.state.power -= 16
                else:
                    self.state.power = 0

                self.state.lives -= 1
                if self.state.lives < 0:
                    #TODO: display a menu to ask the players if they want to continue.
                    self._game.continues -= 1
                    if self._game.continues < 0:
                        raise GameOver

                    for i in range(5):
                        self._game.drop_bonus(self.state.x, self.state.y, 4,
                                              end_pos=(self._game.prng.rand_double() * 288 + 48,
                                                       self._game.prng.rand_double() * 192 - 64))
                    self.state.score = 0
                    self.state.effective_score = 0
                    self.state.lives = 2 #TODO: use the right default.
                    self.state.bombs = 3 #TODO: use the right default.
                    self.state.power = 0

                    self.state.graze = 0
                    self.state.points = 0
                else:
                    self._game.drop_bonus(self.state.x, self.state.y, 2,
                                          end_pos=(self._game.prng.rand_double() * 288 + 48, # 102h.exe@0x41f3dc
                                                   self._game.prng.rand_double() * 192 - 64))        # @0x41f3
                    for i in range(5):
                        self._game.drop_bonus(self.state.x, self.state.y, 0,
                                              end_pos=(self._game.prng.rand_double() * 288 + 48,
                                                       self._game.prng.rand_double() * 192 - 64))

            elif time == 7:
                self.sprite.mirrored = False
                self.sprite.blendfunc = 0
                self.sprite.rescale = 0.75, 1.5
                self.sprite.fade(26, 96, lambda x: x)
                self.sprite.scale_in(26, 0.00, 2.5, lambda x: x)

            elif time == 32:
                self.state.x = float(self._game.width) / 2. #TODO
                self.state.y = float(self._game.width) #TODO
                self.direction = None

                self.sprite = Sprite()
                self.anmrunner = ANMRunner(self.anm_wrapper, 0, self.sprite)
                self.sprite.alpha = 128
                self.sprite.rescale = 0.0, 2.5
                self.sprite.fade(30, 255, lambda x: x)
                self.sprite.blendfunc = 1
                self.sprite.scale_in(30, 1., 1., lambda x: x)
                self.anmrunner.run_frame()

            elif time == 61: # respawned
                self.state.touchable = True
                self.state.invulnerable_time = 240
                self.sprite.blendfunc = 0
                self.sprite.changed = True

            if time > 30:
                self._game.cancel_bullets()

            if time > 90: # start the bullet hell again
                self.death_time = 0

        self.anmrunner.run_frame()

