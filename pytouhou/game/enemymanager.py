from itertools import chain
from io import BytesIO
import os
from struct import unpack, pack
from pytouhou.utils.interpolator import Interpolator
from pytouhou.game.sprite import Sprite
from math import cos, sin, atan2


class Enemy(object):
    def __init__(self, pos, life, _type, script, anm_wrapper):
        self.anm_wrapper = anm_wrapper
        self.anm = None
        self.script = list(script)
        self.x, self.y = pos
        self.life = life
        self.type = _type
        self.frame = 0
        self.sprite = None

        self.movement_dependant_sprites = None
        self.interpolator = None #TODO
        self.angle = 0.
        self.speed = 0.
        self.rotation_speed = 0.
        self.acceleration = 0.


    def update(self, frame):
        if not self.script:
            return True
        if self.script[0][0] == self.frame:
            for instr_type, rank_mask, param_mask, args  in self.script.pop(0)[1]:
                if instr_type == 1: # delete
                    return False
                elif instr_type == 97: # set_enemy_sprite
                    script_index, = unpack('<I', args)
                    self.anm, self.sprite = self.anm_wrapper.get_sprite(script_index)
                elif instr_type == 98: #TODO
                    self.movement_dependant_sprites = unpack('<HHHHI', args)
                elif instr_type == 43: # set_pos
                    self.x, self.y, z = unpack('<fff', args)
                    self.interpolator = Interpolator((self.x, self.y)) #TODO: better interpolation
                    self.interpolator.set_interpolation_start(self.frame, (self.x, self.y))
                elif instr_type == 45: # set_angle_speed
                    self.angle, self.speed = unpack('<ff', args)
                elif instr_type == 46: # set_angle
                    self.rotation_speed, = unpack('<f', args)
                elif instr_type == 47: # set_speed
                    self.speed, = unpack('<f', args)
                elif instr_type == 48: # set_acceleration
                    self.acceleration, = unpack('<f', args)
                elif instr_type == 51: # move_towards_player #TODO: main
                    unknown, self.speed = unpack('<If', args) #TODO: unknown
                    player_x, player_y = 192., 400.#TODO
                    self.angle = atan2(player_y - self.y, player_x - self.x)
                elif instr_type == 57:
                    duration, x, y, z = unpack('<Ifff', args)
                    self.interpolator.set_interpolation_end(self.frame + duration, (x, y))

        x, y = self.x, self.y
        if self.interpolator:
            self.interpolator.update(self.frame)
            x, y = self.interpolator.values

        self.speed += self.acceleration #TODO: units? Execution order?
        self.angle += self.rotation_speed #TODO: units? Execution order?

        dx, dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed
        if self.type & 2:
            x -= dx
        else:
            x += dx
        y += dy

        if self.movement_dependant_sprites:
            #TODO: is that really how it works?
            dx, dy = self.x - x, self.y - y
            if (dx, dy) == (0, 0):
                self.anm, self.sprite = self.anm_wrapper.get_sprite(self.movement_dependant_sprites[0])
            elif abs(dx) > abs(dy):
                if dx < 0:
                    self.anm, self.sprite = self.anm_wrapper.get_sprite(self.movement_dependant_sprites[2])
                else:
                    self.anm, self.sprite = self.anm_wrapper.get_sprite(self.movement_dependant_sprites[3])
            else:
                if dy < 0:
                    self.anm, self.sprite = self.anm_wrapper.get_sprite(self.movement_dependant_sprites[1])
                else:
                    self.anm, self.sprite = self.anm_wrapper.get_sprite(self.movement_dependant_sprites[2])

        self.x, self.y = x, y
        if self.sprite:
            self.sprite.update()

        self.frame += 1
        return True



class EnemyManager(object):
    def __init__(self, stage, anm_wrapper, ecl):
        self.stage = stage
        self.anm_wrapper = anm_wrapper
        self.main = []
        self.subs = {}
        self.objects_by_texture = {}
        self.enemies = []

        # Populate main
        for frame, sub, instr_type, args in ecl.main:
            if not self.main or self.main[-1][0] < frame:
                self.main.append((frame, [(sub, instr_type, args)]))
            elif self.main[-1][0] == frame:
                self.main[-1][1].append((sub, instr_type, args))


        # Populate subs
        for i, sub in enumerate(ecl.subs):
            for frame, instr_type, rank_mask, param_mask, args in sub:
                if i not in self.subs:
                    self.subs[i] = []
                if not self.subs[i] or self.subs[i][-1][0] < frame:
                    self.subs[i].append((frame, [(instr_type, rank_mask, param_mask, args)]))
                elif self.subs[i][-1][0] == frame:
                    self.subs[i][-1][1].append((instr_type, rank_mask, param_mask, args))


    def update(self, frame):
        if self.main and self.main[0][0] == frame:
            for sub, instr_type, args in self.main.pop(0)[1]:
                if instr_type in (0, 2, 4, 6): # Normal/mirrored enemy
                    x, y, z, life, unknown1, unknown2, unknown3 = args
                    self.enemies.append(Enemy((x, y), life, instr_type, self.subs[sub], self.anm_wrapper))

        # Update enemies
        for enemy in tuple(self.enemies):
            if not enemy.update(frame):
                self.enemies.remove(enemy)
                continue

        # Add enemies to vertices/uvs
        self.objects_by_texture = {}
        for enemy in self.enemies:
            ox, oy = enemy.x, enemy.y
            if enemy.sprite:
                key = enemy.anm.first_name, enemy.anm.secondary_name
                if not key in self.objects_by_texture:
                    self.objects_by_texture[key] = (0, [], [])
                vertices = tuple((x + ox, y + oy, z) for x, y, z in enemy.sprite._vertices)
                self.objects_by_texture[key][2].extend(enemy.sprite._uvs)
                self.objects_by_texture[key][1].extend(vertices)
        for key, (nb_vertices, vertices, uvs) in self.objects_by_texture.items():
            nb_vertices = len(vertices)
            vertices = pack('f' * (3 * nb_vertices), *chain(*vertices))
            uvs = pack('f' * (2 * nb_vertices), *chain(*uvs))
            self.objects_by_texture[key] = (nb_vertices, vertices, uvs)

