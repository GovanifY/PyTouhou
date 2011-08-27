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
from io import BytesIO
import os
from struct import unpack, pack
from pytouhou.utils.interpolator import Interpolator
from pytouhou.vm.eclrunner import ECLRunner
from pytouhou.vm.anmrunner import ANMRunner
from pytouhou.game.sprite import Sprite
from math import cos, sin, atan2


class Enemy(object):
    def __init__(self, pos, life, _type, anm_wrapper):
        self._anm_wrapper = anm_wrapper
        self._sprite = None
        self._anmrunner = None
        self._removed = False
        self._type = _type
        self._was_visible = False

        self.frame = 0

        self.x, self.y = pos
        self.life = life
        self.max_life = life
        self.touchable = True
        self.damageable = True
        self.death_flags = 0
        self.pending_bullets = []
        self.bullet_attributes = None
        self.bullet_launch_offset = (0, 0)
        self.death_callback = None
        self.low_life_callback = None
        self.low_life_trigger = None
        self.timeout = None
        self.timeout_callback = None
        self.remaining_lives = -1

        self.bullet_launch_interval = 0
        self.delay_attack = False

        self.death_anim = None
        self.movement_dependant_sprites = None
        self.direction = None
        self.interpolator = None #TODO
        self.speed_interpolator = None
        self.angle = 0.
        self.speed = 0.
        self.rotation_speed = 0.
        self.acceleration = 0.

        self.hitbox = (0, 0)
        self.screen_box = None


    def set_bullet_attributes(self, type_, bullet_anim, launch_anim,
                              bullets_per_shot, number_of_shots, speed, unknown,
                              launch_angle, angle, flags):
        self.bullet_attributes = (type_, bullet_anim, launch_anim, bullets_per_shot,
                                  number_of_shots, speed, unknown, launch_angle,
                                  angle, flags)
        if not self.delay_attack:
            self.fire()


    def fire(self):
        #TODO
        pass


    def select_player(self, players):
        return players[0] #TODO


    def get_player_angle(self, player):
        return atan2(player.y - self.y, player.x - self.x)


    def set_anim(self, index):
        self._sprite = Sprite()
        self._anmrunner = ANMRunner(self._anm_wrapper, index, self._sprite)


    def set_pos(self, x, y, z):
        self.x, self.y = x, y
        self.interpolator = Interpolator((x, y))
        self.interpolator.set_interpolation_start(self.frame, (x, y))


    def move_to(self, duration, x, y, z, formula):
        if not self.interpolator:
            self.interpolator = Interpolator((self.x, self.y), formula)
            self.interpolator.set_interpolation_start(self.frame, (self.x, self.y))
            self.interpolator.set_interpolation_end(self.frame + duration - 1, (x, y))


    def stop_in(self, duration):
        #TODO: interpolation method and start/stop frame
        # See 97 vs 98 anim conflict
        if not self.speed_interpolator:
            self.speed_interpolator = Interpolator((self.speed,))
            self.speed_interpolator.set_interpolation_start(self.frame, (self.speed,))
            self.speed_interpolator.set_interpolation_end(self.frame + duration, (0.,))


    def is_visible(self, screen_width, screen_height):
        if not self._sprite:
            return False

        tx, ty, tw, th = self._sprite.texcoords
        if self._sprite.corner_relative_placement:
            raise Exception #TODO
        else:
            max_x = tw / 2.
            max_y = th / 2.
            min_x = -max_x
            min_y = -max_y

        if any((min_x > screen_width - self.x,
                max_x < -self.x,
                min_y > screen_height - self.y,
                max_y < -self.y)):
            return False
        return True


    def get_objects_by_texture(self):
        objects_by_texture = {}
        key = self._sprite.anm.first_name, self._sprite.anm.secondary_name
        key = (key, self._sprite.blendfunc)
        if not key in objects_by_texture:
            objects_by_texture[key] = (0, [], [], [])
        vertices = tuple((x + self.x, y + self.y, z) for x, y, z in self._sprite._vertices)
        objects_by_texture[key][1].extend(vertices)
        objects_by_texture[key][2].extend(self._sprite._uvs)
        objects_by_texture[key][3].extend(self._sprite._colors)
        #TODO: effects/bullet launch
        return objects_by_texture


    def update(self):
        x, y = self.x, self.y
        if self.interpolator:
            self.interpolator.update(self.frame)
            x, y = self.interpolator.values

        self.speed += self.acceleration #TODO: units? Execution order?
        self.angle += self.rotation_speed #TODO: units? Execution order?


        if self.speed_interpolator:
            self.speed_interpolator.update(self.frame)
            self.speed, = self.speed_interpolator.values


        dx, dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed
        if self._type & 2:
            x -= dx
        else:
            x += dx
        y += dy

        if self.movement_dependant_sprites:
            #TODO: is that really how it works? Almost.
            # Sprite determination is done only once per changement, and is
            # superseeded by ins_97.
            end_left, end_right, left, right = self.movement_dependant_sprites
            if x < self.x and self.direction != -1:
                self.set_anim(left)
                self.direction = -1
            elif x > self.x and self.direction != +1:
                self.set_anim(right)
                self.direction = +1
            elif x == self.x and self.direction is not None:
                self.set_anim({-1: end_left, +1: end_right}[self.direction])
                self.direction = None


        if self.screen_box:
            xmin, ymin, xmax, ymax = self.screen_box
            x = max(xmin, min(x, xmax))
            y = max(ymin, min(y, ymax))


        self.x, self.y = x, y

        #TODO
        if self._anmrunner and not self._anmrunner.run_frame():
            self._anmrunner = None

        if self._sprite:
            if self._sprite._removed:
                self._sprite = None
            else:
                self._sprite.update()
                if self._sprite._changed:
                    self._sprite.update_vertices_uvs_colors()

        self.frame += 1



class EnemyManager(object):
    def __init__(self, stage, anm_wrapper, ecl, game_state):
        self._game_state = game_state
        self.stage = stage
        self.anm_wrapper = anm_wrapper
        self.main = []
        self.ecl = ecl
        self.objects_by_texture = {}
        self.enemies = []
        self.processes = []

        # Populate main
        for frame, sub, instr_type, args in ecl.main:
            if not self.main or self.main[-1][0] < frame:
                self.main.append((frame, [(sub, instr_type, args)]))
            elif self.main[-1][0] == frame:
                self.main[-1][1].append((sub, instr_type, args))


    def update(self, frame):
        if self.main and self.main[0][0] == frame:
            for sub, instr_type, args in self.main.pop(0)[1]:
                if instr_type in (0, 2, 4, 6): # Normal/mirrored enemy
                    x, y, z, life, unknown1, unknown2, unknown3 = args
                    if instr_type & 4:
                        if x < -990: #102h.exe@0x411820
                            x = self._game_state.prng.rand_double() * 368
                        if y < -990: #102h.exe@0x41184b
                            y = self._game_state.prng.rand_double() * 416
                        if z < -990: #102h.exe@0x411881
                            y = self._game_state.prng.rand_double() * 800
                    enemy = Enemy((x, y), life, instr_type, self.anm_wrapper)
                    self.enemies.append(enemy)
                    self.processes.append(ECLRunner(self.ecl, sub, enemy, self._game_state))


        # Run processes
        self.processes[:] = (process for process in self.processes if process.run_iteration())

        # Filter of destroyed enemies
        self.enemies[:] = (enemy for enemy in self.enemies if not enemy._removed)

        # Update enemies
        for enemy in self.enemies:
            enemy.update()

        # Filter out non-visible enemies
        visible_enemies = [enemy for enemy in self.enemies if enemy.is_visible(384, 448)] #TODO
        for enemy in visible_enemies:
            enemy._was_visible = True

        # Filter out-of-screen enemies
        for enemy in tuple(self.enemies):
            if enemy._was_visible and not enemy in visible_enemies:
                enemy._removed = True
                self.enemies.remove(enemy)

        #TODO: disable boss mode if it is dead/it has timeout
        if self._game_state.boss and self._game_state.boss._removed:
            self._game_state.boss = None

        # Add enemies to vertices/uvs
        self.objects_by_texture = {}
        for enemy in visible_enemies:
            if enemy.is_visible(384, 448): #TODO
                for key, (count, vertices, uvs, colors) in enemy.get_objects_by_texture().items():
                    if not key in self.objects_by_texture:
                        self.objects_by_texture[key] = (0, [], [], [])
                    self.objects_by_texture[key][1].extend(vertices)
                    self.objects_by_texture[key][2].extend(uvs)
                    self.objects_by_texture[key][3].extend(colors)
        for key, (nb_vertices, vertices, uvs, colors) in self.objects_by_texture.items():
            nb_vertices = len(vertices)
            vertices = pack('f' * (3 * nb_vertices), *chain(*vertices))
            uvs = pack('f' * (2 * nb_vertices), *chain(*uvs))
            colors = pack('B' * (4 * nb_vertices), *chain(*colors))
            self.objects_by_texture[key] = (nb_vertices, vertices, uvs, colors)

