#!/usr/bin/env python
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

import sys
import os

import struct
from math import degrees, radians
from io import BytesIO
from itertools import chain

import pygame

from pytouhou.formats.pbg3 import PBG3
from pytouhou.formats.std import Stage
from pytouhou.formats.ecl import ECL
from pytouhou.formats.anm0 import Animations
from pytouhou.game.sprite import AnmWrapper
from pytouhou.game.background import Background
from pytouhou.game.enemymanager import EnemyManager
from pytouhou.opengl.texture import TextureManager
from pytouhou.game.game import GameState
from pytouhou.game.player import Player

import OpenGL
OpenGL.FORWARD_COMPATIBLE_ONLY = True
from OpenGL.GL import *
from OpenGL.GLU import *


def main(path, stage_num):
    # Initialize pygame
    pygame.init()
    window = pygame.display.set_mode((384, 448), pygame.OPENGL | pygame.DOUBLEBUF)

    # Initialize OpenGL
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(30, float(window.get_width())/window.get_height(), 101010101./2010101., 101010101./10101.)

    glEnable(GL_BLEND)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_FOG)
    glHint(GL_FOG_HINT, GL_NICEST)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnableClientState(GL_COLOR_ARRAY)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    # Load data
    with open(path, 'rb') as file:
        archive = PBG3.read(file)
        texture_manager = TextureManager(archive)

        stage = Stage.read(BytesIO(archive.extract('stage%d.std' % stage_num)), stage_num)

        ecl = ECL.read(BytesIO(archive.extract('ecldata%d.ecl' % stage_num)))
        enemies_anim = Animations.read(BytesIO(archive.extract('stg%denm.anm' % stage_num)))
        anims = [enemies_anim]
        try:
            enemies2_anim = Animations.read(BytesIO(archive.extract('stg%denm2.anm' % stage_num)))
        except KeyError:
            pass
        else:
            anims.append(enemies2_anim)
        enemy_manager = EnemyManager(stage, AnmWrapper(anims), ecl, GameState([Player()], stage_num, 0, 16))
        texture_manager.preload(anims)

        background_anim = Animations.read(BytesIO(archive.extract('stg%dbg.anm' % stage_num)))
        background = Background(stage, AnmWrapper((background_anim,)))
        texture_manager.preload((background_anim,))

        print(enemy_manager.stage.name)

        frame = 0

        # Main loop
        clock = pygame.time.Clock()
        while True:
            # Check events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q)):
                    sys.exit(0)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT:
                        pygame.display.toggle_fullscreen()

            # Update game
            enemy_manager.update(frame)
            background.update(frame)

            # Draw everything
#            glClearColor(0.0, 0.0, 1.0, 0)
            glClear(GL_DEPTH_BUFFER_BIT)

            fog_b, fog_g, fog_r, _, fog_start, fog_end = background.fog_interpolator.values
            x, y, z = background.position_interpolator.values
            dx, dy, dz = background.position2_interpolator.values

            glFogi(GL_FOG_MODE, GL_LINEAR)
            glFogf(GL_FOG_START, fog_start)
            glFogf(GL_FOG_END,  fog_end)
            glFogfv(GL_FOG_COLOR, (fog_r / 255., fog_g / 255., fog_b / 255., 1.))

            #TODO
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            # Some explanations on the magic constants:
            # 192. = 384. / 2. = width / 2.
            # 224. = 448. / 2. = height / 2.
            # 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
            # This is so that objects on the (O, x, y) plane use pixel coordinates
            gluLookAt(192., 224., - 835.979370 * dz,
                      192. + dx, 224. - dy, 0., 0., -1., 0.)
            #print(glGetFloat(GL_MODELVIEW_MATRIX))
            glTranslatef(-x, -y, -z)

            glEnable(GL_DEPTH_TEST)
            for texture_key, (nb_vertices, vertices, uvs, colors) in background.objects_by_texture.items():
                glBindTexture(GL_TEXTURE_2D, texture_manager[texture_key])
                glVertexPointer(3, GL_FLOAT, 0, vertices)
                glTexCoordPointer(2, GL_FLOAT, 0, uvs)
                glColorPointer(4, GL_UNSIGNED_BYTE, 0, colors)
                glDrawArrays(GL_QUADS, 0, nb_vertices)
            glDisable(GL_DEPTH_TEST)

            #TODO
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            # Some explanations on the magic constants:
            # 192. = 384. / 2. = width / 2.
            # 224. = 448. / 2. = height / 2.
            # 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
            # This is so that objects on the (O, x, y) plane use pixel coordinates
            gluLookAt(192., 224., - 835.979370,
                      192., 224., 0., 0., -1., 0.)

            glDisable(GL_FOG)
            for texture_key, (nb_vertices, vertices, uvs, colors) in enemy_manager.objects_by_texture.items():
                glBindTexture(GL_TEXTURE_2D, texture_manager[texture_key])
                glVertexPointer(3, GL_FLOAT, 0, vertices)
                glTexCoordPointer(2, GL_FLOAT, 0, uvs)
                glColorPointer(4, GL_UNSIGNED_BYTE, 0, colors)
                glDrawArrays(GL_QUADS, 0, nb_vertices)
            glEnable(GL_FOG)

            pygame.display.flip()
            clock.tick(120)
            frame += 1



try:
    file_path, stage_num = sys.argv[1:]
    stage_num = int(stage_num)
except ValueError:
    print('Usage: %s std_dat_path stage_num' % sys.argv[0])
else:
    main(file_path, stage_num)

