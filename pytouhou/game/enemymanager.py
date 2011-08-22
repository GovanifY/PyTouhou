from itertools import chain
from io import BytesIO
import os
from struct import unpack, pack
from pytouhou.utils.interpolator import Interpolator
from pytouhou.game.eclrunner import ECLRunner
from pytouhou.game.sprite import Sprite
from math import cos, sin, atan2


from pytouhou.utils.random import Random
random = Random(0x39f4)


class Enemy(object):
    def __init__(self, pos, life, _type, anm_wrapper):
        self._anm_wrapper = anm_wrapper
        self._anm = None
        self._sprite = None
        self._removed = False
        self._type = _type

        self.frame = 0

        self.x, self.y = pos
        self.life = life
        self.max_life = life
        self.pending_bullets = []
        self.bullet_attributes = None
        self.bullet_launch_offset = (0, 0)
        self.vulnerable = True
        self.death_callback = None
        self.low_life_callback = None
        self.low_life_trigger = None
        self.timeout = None
        self.remaining_lives = -1

        self.bullet_launch_interval = 0
        self.delay_attack = False

        self.death_anim = None
        self.movement_dependant_sprites = None
        self.direction = None
        self.interpolator = None #TODO
        self.angle = 0.
        self.speed = 0.
        self.rotation_speed = 0.
        self.acceleration = 0.

        self.hitbox = (0, 0)


    def set_bullet_attributes(self, bullet_anim, launch_anim, bullets_per_shot,
                              number_of_shots, speed, unknown, launch_angle,
                              angle, flags):
        self.bullet_attributes = (1, bullet_anim, launch_anim, bullets_per_shot,
                                  number_of_shots, speed, unknown, launch_angle,
                                  angle, flags)
        if not self.delay_attack:
            pass
            #TODO: actually fire


    def set_anim(self, index):
        self._anm, self._sprite = self._anm_wrapper.get_sprite(index)


    def set_pos(self, x, y, z):
        self.x, self.y = x, y
        self.interpolator = Interpolator((x, y))
        self.interpolator.set_interpolation_start(self.frame, (x, y))


    def move_to(self, duration, x, y, z):
        self.interpolator.set_interpolation_end(self.frame + duration, (x, y))


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

        if any((min_x >= screen_width - self.x,
                max_x <= -self.x,
                min_y >= screen_height - self.y,
                max_y <= -self.y)):
            return False
        return True


    def get_objects_by_texture(self):
        objects_by_texture = {}
        key = self._anm.first_name, self._anm.secondary_name
        if not key in objects_by_texture:
            objects_by_texture[key] = (0, [], [], [])
        vertices = tuple((x + self.x, y + self.y, z) for x, y, z in self._sprite._vertices)
        objects_by_texture[key][1].extend(vertices)
        objects_by_texture[key][2].extend(self._sprite._uvs)
        objects_by_texture[key][3].extend(self._sprite._colors)
        #TODO: effects/bullet launch
        return objects_by_texture


    def update(self, frame):
        x, y = self.x, self.y
        if self.interpolator:
            self.interpolator.update(self.frame)
            x, y = self.interpolator.values

        self.speed += self.acceleration #TODO: units? Execution order?
        self.angle += self.rotation_speed #TODO: units? Execution order?

        dx, dy = cos(self.angle) * self.speed, sin(self.angle) * self.speed
        if self._type & 2:
            x -= dx
        else:
            x += dx
        y += dy

        if self.movement_dependant_sprites:
            #TODO: is that really how it works?
            if x < self.x:
                self.set_anim(self.movement_dependant_sprites[2])
                self.direction = -1
            elif x > self.x:
                self.set_anim(self.movement_dependant_sprites[3])
                self.direction = +1
            elif self.direction is not None:
                self.set_anim(self.movement_dependant_sprites[{-1: 0, +1:1}[self.direction]])
                self.direction = None

        self.x, self.y = x, y
        if self._sprite:
            changed = self._sprite.update()
            visible = self.is_visible(384, 448)
            if changed and visible:
                self._sprite.update_vertices_uvs_colors()
            elif not self._sprite.playing:
                visible = False
                self._sprite = None
        else:
            visible = False


        self.frame += 1
        return visible



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
                        if x < -990:
                            x = random.rand_double() * 368 #102h.exe@0x411820
                        if y < -990:
                            y = random.rand_double() * 416 #102h.exe@0x41184b
                        if z < -990:
                            y = random.rand_double() * 800 #102h.exe@0x411881
                    enemy = Enemy((x, y), life, instr_type, self.anm_wrapper)
                    self.enemies.append(enemy)
                    self.processes.append(ECLRunner(self.ecl, sub, enemy, self._game_state))


        # Run processes
        self.processes[:] = (process for process in self.processes if process.run_iteration())

        # Filter of destroyed enemies
        self.enemies[:] = (enemy for enemy in self.enemies if not enemy._removed)

        # Update enemies
        visible_enemies = [enemy for enemy in self.enemies if enemy.update(frame)]

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

