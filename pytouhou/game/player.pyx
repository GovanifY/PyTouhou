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

from libc.math cimport M_PI as pi

from pytouhou.game.sprite cimport Sprite
from pytouhou.vm.anmrunner import ANMRunner
from pytouhou.game.bullettype cimport BulletType
from pytouhou.game.bullet cimport Bullet
from pytouhou.game.lasertype cimport LaserType
from pytouhou.game.laser cimport PlayerLaser


class GameOver(Exception):
    pass


cdef class PlayerState:
    def __init__(self, long number, long character=0, long score=0,
                 long power=0, long lives=2, long bombs=3, long continues=0):
        self.number = number
        self.character = character # ReimuA/ReimuB/MarisaA/MarisaB/...

        self.score = score
        self.effective_score = score
        self.lives = lives
        self.bombs = bombs
        self.power = power
        self.continues = continues

        self.continues_used = 0
        self.miss = 0
        self.bombs_used = 0

        self.graze = 0
        self.points = 0

        self.x = 192.0
        self.y = 384.0

        self.invulnerable_time = 240
        self.touchable = True
        self.focused = False

        self.power_bonus = 0 # Never goes over 30.


cdef class Player(Element):
    def __init__(self, PlayerState state, Game game, anm):
        Element.__init__(self)

        self._game = game
        self.anm = anm

        self.speeds = (self.sht.horizontal_vertical_speed,
                       self.sht.diagonal_speed,
                       self.sht.horizontal_vertical_focused_speed,
                       self.sht.diagonal_focused_speed)

        self.fire_time = 0

        self.state = state
        self.direction = 0

        self.set_anim(0)

        self.death_time = 0


    cdef void set_anim(self, index):
        self.sprite = Sprite()
        self.anmrunner = ANMRunner(self.anm, index, self.sprite)


    cdef void play_sound(self, str name):
        self._game.sfx_player.play('%s.wav' % name)


    cdef void collide(self):
        if not self.state.invulnerable_time and not self.death_time and self.state.touchable: # Border Between Life and Death
            self.death_time = self._game.frame
            self._game.new_effect((self.state.x, self.state.y), 17)
            self._game.modify_difficulty(-1600)
            self.play_sound('pldead00')
            for i in xrange(16):
                self._game.new_particle((self.state.x, self.state.y), 11, 256) #TODO: find the real size and range.


    def start_focusing(self):
        self.state.focused = True


    def stop_focusing(self):
        self.state.focused = False


    cdef void fire(self):
        cdef double x, y
        cdef long shot_power

        sht = self.focused_sht if self.state.focused else self.sht

        # Don’t use min() since sht.shots could be an empty dict.
        power = 999
        for shot_power in sht.shots:
            if self.state.power < shot_power:
                power = power if power < shot_power else shot_power

        bullets = self._game.players_bullets
        lasers = self._game.players_lasers
        nb_bullets_max = self._game.nb_bullets_max

        if self.fire_time % 5 == 0:
            self.play_sound('plst00')

        for shot in sht.shots[power]:
            origin = self.orbs[shot.orb - 1] if shot.orb else self.state
            shot_type = <unsigned char>shot.type

            if shot_type == 3:
                if self.fire_time != 30:
                    continue

                #TODO: number can do very surprising things, like removing any
                # bullet creation from enemies with 3. For now, crash when not
                # an actual laser number.
                number = <long>shot.delay
                if lasers[number] is not None:
                    continue

                laser_type = LaserType(self.anm, shot.sprite % 256, 68)
                lasers[number] = PlayerLaser(laser_type, 0, shot.hitbox, shot.damage, shot.angle, shot.speed, shot.interval, origin)
                continue

            if (self.fire_time + shot.delay) % shot.interval != 0:
                continue

            if nb_bullets_max != 0 and len(bullets) == nb_bullets_max:
                break

            x = origin.x + shot.pos[0]
            y = origin.y + shot.pos[1]

            #TODO: find a better way to do that.
            bullet_type = BulletType(self.anm, shot.sprite % 256,
                                     shot.sprite % 256 + 32, #TODO: find the real cancel anim
                                     0, 0, 0, 0.)
            #TODO: Type 1 (homing bullets)
            if shot_type == 2:
                #TODO: triple-check acceleration!
                bullets.append(Bullet((x, y), bullet_type, 0,
                                      shot.angle, shot.speed,
                                      (-1, 0, 0, 0, 0.15, -pi/2., 0., 0.),
                                      16, self, self._game, player=self.state.number,
                                      damage=shot.damage, hitbox=shot.hitbox))
            else:
                bullets.append(Bullet((x, y), bullet_type, 0,
                                      shot.angle, shot.speed,
                                      (0, 0, 0, 0, 0., 0., 0., 0.),
                                      0, self, self._game, player=self.state.number,
                                      damage=shot.damage, hitbox=shot.hitbox))


    cpdef update(self, long keystate):
        cdef double dx, dy

        if self.death_time == 0 or self._game.frame - self.death_time > 60:
            speed, diag_speed = self.speeds[2:] if self.state.focused else self.speeds[:2]
            try:
                dx, dy = {16: (0., -speed), 32: (0., speed), 64: (-speed, 0.), 128: (speed, 0.),
                          16|64: (-diag_speed, -diag_speed), 16|128: (diag_speed, -diag_speed),
                          32|64: (-diag_speed, diag_speed), 32|128:  (diag_speed, diag_speed)}[keystate & (16|32|64|128)]
            except KeyError:
                dx, dy = 0., 0.

            if dx < 0 and self.direction != -1:
                self.set_anim(1)
                self.direction = -1
            elif dx > 0 and self.direction != +1:
                self.set_anim(3)
                self.direction = +1
            elif dx == 0 and self.direction != 0:
                self.set_anim({-1: 2, +1: 4}[self.direction])
                self.direction = 0

            self.state.x += dx
            self.state.y += dy

            #XXX
            self.x = self.state.x
            self.y = self.state.y

            if self.state.x < 8.:
                self.state.x = 8.
            if self.state.x > self._game.width - 8:
                self.state.x = self._game.width - 8.
            if self.state.y < 16.:
                self.state.y = 16.
            if self.state.y > self._game.height - 16:
                self.state.y = self._game.height -16.

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

            if keystate & 2 and self.bomb_time == 0:
                self._game.set_player_bomb()
                self.bomb_time = 240
            if self.bomb_time > 0:
                self.bomb_time -= 1
                if self.bomb_time == 0:
                    self._game.unset_player_bomb()

        if self.death_time:
            time = self._game.frame - self.death_time
            if time == 6: # too late, you are dead :(
                self.state.touchable = False
                if self.state.power > 16:
                    self.state.power -= 16
                else:
                    self.state.power = 0
                self._game.cancel_player_lasers()

                self.state.miss += 1
                self.state.lives -= 1
                if self.state.lives < 0:
                    #TODO: display a menu to ask the players if they want to continue.
                    if self.state.continues == 0:
                        raise GameOver

                    # Don’t decrement if it’s infinite.
                    if self.state.continues >= 0:
                        self.state.continues -= 1
                    self.state.continues_used += 1

                    for i in xrange(5):
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
                    for i in xrange(5):
                        self._game.drop_bonus(self.state.x, self.state.y, 0,
                                              end_pos=(self._game.prng.rand_double() * 288 + 48,
                                                       self._game.prng.rand_double() * 192 - 64))

            elif time == 7:
                self.sprite.mirrored = False
                self.sprite.blendfunc = 0
                self.sprite.rescale = 0.75, 1.5
                self.sprite.fade(26, 96)
                self.sprite.scale_in(26, 0., 2.5)

            #TODO: the next two branches could be happening at the same frame.
            elif time == 31:
                self._game.cancel_bullets()

            elif time == 32:
                self.state.x = float(self._game.width) / 2. #TODO
                self.state.y = float(self._game.width) #TODO
                self.direction = 0

                self.sprite = Sprite()
                self.anmrunner = ANMRunner(self.anm, 0, self.sprite)
                self.sprite.alpha = 128
                self.sprite.rescale = 0., 2.5
                self.sprite.fade(30, 255)
                self.sprite.blendfunc = 1
                self.sprite.scale_in(30, 1., 1.)

            elif time == 61: # respawned
                self.state.touchable = True
                self.state.invulnerable_time = 240
                self.sprite.blendfunc = 0
                self.sprite.changed = True

            elif time == 91: # start the bullet hell again
                self.death_time = 0

        self.anmrunner.run_frame()

