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

from math import radians
from pytouhou.vm import spawn_enemy
from pytouhou.game import NextStage


def disk(enemy, game):
    if enemy.frame == 0:
        enemy.set_anim(0)

        enemy.set_hitbox(32, 32)

        enemy.death_anim = 1

        enemy.update_mode = 0
        enemy.angle, enemy.speed = radians(90), 1.5

    elif enemy.frame == 10000:
        enemy.removed = True


def boss(enemy, game):
    if enemy.frame == 0:
        enemy.set_anim(3)
        enemy.set_hitbox(8, 32)
        enemy.death_flags = 1
        enemy.set_boss(True)

        enemy.timeout = 20 * 60
        enemy.timeout_callback.enable(some_spellcard, (enemy, game))

        enemy.low_life_trigger = 0x40
        enemy.low_life_callback.enable(some_spellcard, (enemy, game))

    elif enemy.frame == 10000:
        enemy.removed = True

    if enemy.frame % 10 == 0:
        enemy.set_bullet_attributes(67, 0, 0, 3 if game.spellcard is not None else 1, 1, 6., 6., 0., radians(3), 0)


def some_spellcard(enemy, game):
    enemy.life = 0x40
    enemy.difficulty_coeffs = (-.5, .5, 0, 0, 0, 0)
    game.change_bullets_into_star_items()
    game.spellcard = (42, 'Some Spellcard', 0)
    game.enable_spellcard_effect()

    enemy.timeout = 10 * 60
    enemy.timeout_callback.enable(on_boss_death, (enemy, game))
    enemy.death_callback.enable(on_boss_death, (enemy, game))
    enemy.low_life_callback.disable()


def on_boss_death(enemy, game):
    enemy.timeout_callback.disable()
    enemy.death_callback.disable()
    game.disable_spellcard_effect()
    enemy.removed = True

    raise NextStage


def stage1(game):
    if game.frame == 0x10:
        spawn_enemy(game, disk, x=50., y=-32., life=20, score=300)
    elif game.frame == 0x20:
        spawn_enemy(game, disk, x=60., y=-32., life=20, score=300)
    elif game.frame == 0x30:
        spawn_enemy(game, disk, x=70., y=-32., life=20, score=300)
    elif game.frame == 0x40:
        spawn_enemy(game, disk, x=80., y=-32., life=20, score=300)
    elif game.frame == 0x50:
        spawn_enemy(game, disk, x=90., y=-32., life=20, score=300)
    elif game.frame == 0x60:
        spawn_enemy(game, disk, x=100., y=-32., life=20, score=300)
    elif game.frame == 0x100:
        spawn_enemy(game, boss, x=192., y=64., life=1000, item=-2, score=10000)
