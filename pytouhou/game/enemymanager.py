from itertools import chain
from io import BytesIO
import os
from struct import unpack, pack
from pytouhou.utils.interpolator import Interpolator
from pytouhou.game.eclrunner import ECLRunner
from pytouhou.game.sprite import Sprite
from math import cos, sin, atan2


class Enemy(object):
    def __init__(self, pos, life, _type, ecl_runner, anm_wrapper):
        self.anm_wrapper = anm_wrapper
        self.anm = None
        self.ecl_runner = ecl_runner
        self.x, self.y = pos
        self.life = life
        self.max_life = life
        self.type = _type
        self.frame = 0
        self.sprite = None
        self.pending_bullets = []
        self.bullet_attributes = []
        self.bullet_launch_offset = (0, 0)

        self.death_sprite = None
        self.movement_dependant_sprites = None
        self.direction = None
        self.interpolator = None #TODO
        self.angle = 0.
        self.speed = 0.
        self.rotation_speed = 0.
        self.acceleration = 0.

        self.hitbox = (0, 0)

        self.ecl_runner.implementation.update({#67: ('HHIIffffI', self.set_bullet_attributes),
                                               97: ('I', self.set_sprite),
                                               98: ('HHHHHH', self.set_multiple_sprites),
                                               45: ('ff', self.set_angle_speed),
                                               43: ('fff', self.set_pos),
                                               46: ('f', self.set_rotation_speed),
                                               47: ('f', self.set_speed),
                                               48: ('f', self.set_acceleration),
                                               51: ('If', self.target_player),
                                               57: ('Ifff', self.move_to),
                                               100: ('I', self.set_death_sprite),
                                               103: ('fff', self.set_hitbox)}) #TODO



    def set_death_sprite(self, sprite_index):
        self.death_sprite = sprite_index % 256 #TODO


    def set_hitbox(self, width, height, depth):
        self.hitbox = (width, height)


    def set_sprite(self, sprite_index):
        self.anm, self.sprite = self.anm_wrapper.get_sprite(sprite_index)


    def set_multiple_sprites(self, default, end_left, end_right, left, right, unknown):
        self.movement_dependant_sprites = end_left, end_right, left, right, unknown
        self.anm, self.sprite = self.anm_wrapper.get_sprite(default)


    def set_angle_speed(self, angle, speed):
        self.angle, self.speed = angle, speed


    def set_pos(self, x, y, z):
        self.x, self.y = x, y
        self.interpolator = Interpolator((x, y))
        self.interpolator.set_interpolation_start(self.frame, (x, y))


    def set_rotation_speed(self, speed):
        self.rotation_speed = speed


    def set_speed(self, speed):
        self.speed = speed


    def set_acceleration(self, acceleration):
        self.acceleration = acceleration


    def target_player(self, unknown, speed):
        self.speed = speed #TODO: unknown
        player_x, player_y = 192., 400.#TODO
        self.angle = atan2(player_y - self.y, player_x - self.x)


    def move_to(self, duration, x, y, z):
        self.interpolator.set_interpolation_end(self.frame + duration, (x, y))


    def is_visible(self, screen_width, screen_height):
        if not self.sprite:
            return False

        tx, ty, tw, th = self.sprite.texcoords
        if self.sprite.corner_relative_placement:
            raise Exception #TODO
        else:
            max_x = tw / 2.
            max_y = th / 2.
            min_x = -max_x
            min_y = -max_y

        if any((min_x >= screen_width - self.x,
                max_x <= -self.x,
                min_y >= screen_height - self.y,
                max_y <= -self.y)):
            return False
        return True


    def get_objects_by_texture(self):
        objects_by_texture = {}
        key = self.anm.first_name, self.anm.secondary_name
        if not key in objects_by_texture:
            objects_by_texture[key] = (0, [], [])
        vertices = tuple((x + self.x, y + self.y, z) for x, y, z in self.sprite._vertices)
        objects_by_texture[key][1].extend(vertices)
        objects_by_texture[key][2].extend(self.sprite._uvs)
        #TODO: effects/bullet launch
        return objects_by_texture


    def update(self, frame):
        self.ecl_runner.update()

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
            if x < self.x:
                self.anm, self.sprite = self.anm_wrapper.get_sprite(self.movement_dependant_sprites[2])
                self.direction = -1
            elif x > self.x:
                self.anm, self.sprite = self.anm_wrapper.get_sprite(self.movement_dependant_sprites[3])
                self.direction = +1
            elif self.direction is not None:
                self.anm, self.sprite = self.anm_wrapper.get_sprite(self.movement_dependant_sprites[{-1: 0, +1:1}[self.direction]])
                self.direction = None

        self.x, self.y = x, y
        if self.sprite:
            changed = self.sprite.update()
            visible = self.is_visible(384, 448)
            if changed and visible:
                self.sprite.update_uvs_vertices()
            elif not self.sprite.playing:
                visible = False
                self.sprite = None
        else:
            visible = False


        self.frame += 1
        return visible



class EnemyManager(object):
    def __init__(self, stage, anm_wrapper, ecl):
        self.stage = stage
        self.anm_wrapper = anm_wrapper
        self.main = []
        self.ecl = ecl
        self.objects_by_texture = {}
        self.enemies = []

        # Populate main
        for frame, sub, instr_type, args in ecl.main:
            if not self.main or self.main[-1][0] < frame:
                self.main.append((frame, [(sub, instr_type, args)]))
            elif self.main[-1][0] == frame:
                self.main[-1][1].append((sub, instr_type, args))


    def make_enemy_deleter(self, enemy):
        def _enemy_deleter(unknown): #TODO: unknown
            self.enemies.remove(enemy)
        return _enemy_deleter


    def update(self, frame):
        if self.main and self.main[0][0] == frame:
            for sub, instr_type, args in self.main.pop(0)[1]:
                if instr_type in (0, 2, 4, 6): # Normal/mirrored enemy
                    x, y, z, life, unknown1, unknown2, unknown3 = args
                    ecl_runner = ECLRunner(self.ecl, sub)
                    enemy = Enemy((x, y), life, instr_type, ecl_runner, self.anm_wrapper)
                    ecl_runner.implementation[1] = ('I', self.make_enemy_deleter(enemy))

                    self.enemies.append(enemy)

        # Update enemies
        visible_enemies = [enemy for enemy in self.enemies if enemy.update(frame)]

        # Add enemies to vertices/uvs
        self.objects_by_texture = {}
        for enemy in visible_enemies:
            if enemy.is_visible(384, 448): #TODO
                for key, (count, vertices, uvs) in enemy.get_objects_by_texture().items():
                    if not key in self.objects_by_texture:
                        self.objects_by_texture[key] = (0, [], [])
                    self.objects_by_texture[key][1].extend(vertices)
                    self.objects_by_texture[key][2].extend(uvs)
        for key, (nb_vertices, vertices, uvs) in self.objects_by_texture.items():
            nb_vertices = len(vertices)
            vertices = pack('f' * (3 * nb_vertices), *chain(*vertices))
            uvs = pack('f' * (2 * nb_vertices), *chain(*uvs))
            self.objects_by_texture[key] = (nb_vertices, vertices, uvs)

