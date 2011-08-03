#!/usr/bin/env python

import sys
import os

import struct
from math import degrees, radians
from io import BytesIO
from itertools import chain

import pygame

import OpenGL
OpenGL.FORWARD_COMPATIBLE_ONLY = True
from OpenGL.GL import *
from OpenGL.GLU import *

from pytouhou.formats.pbg3 import PBG3
from pytouhou.formats.std import Stage
from pytouhou.formats.anm0 import Animations

from pytouhou.utils.matrix import Matrix


def load_texture(image, alpha_image=None):
    textureSurface = pygame.image.load(image).convert_alpha()

    if alpha_image:
        alphaSurface = pygame.image.load(alpha_image)
        assert textureSurface.get_size() == alphaSurface.get_size()
        for x in range(alphaSurface.get_width()):
            for y in range(alphaSurface.get_height()):
                r, g, b, a = textureSurface.get_at((x, y))
                color2 = alphaSurface.get_at((x, y))
                textureSurface.set_at((x, y), (r, g, b, color2[0]))

    textureData = pygame.image.tostring(textureSurface, 'RGBA', 1)

    width = textureSurface.get_width()
    height = textureSurface.get_height()

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA,
        GL_UNSIGNED_BYTE, textureData)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    return texture, width, height



def build_objects_faces(stage, anim):
    objects_faces = []
    for i, obj in enumerate(stage.objects):
        faces = []
        for script_index, x, y, z, width_override, height_override in obj.quads:
            #TODO: move mof of it elsewhere
            vertices = []
            uvs = []
            vertmat = Matrix()
            vertmat.data[0][0] = -.5
            vertmat.data[1][0] = -.5

            vertmat.data[0][1] = .5
            vertmat.data[1][1] = -.5

            vertmat.data[0][2] = .5
            vertmat.data[1][2] = .5

            vertmat.data[0][3] = -.5
            vertmat.data[1][3] = .5

            for i in range(4):
                vertmat.data[2][i] = 0.
                vertmat.data[3][i] = 1.

            properties = {}
            for time, instr_type, data in anim.scripts[script_index]:
                if instr_type == 15:
                    properties[15] = b''
                    break
                elif time == 0: #TODO
                    properties[instr_type] = data
            #if 15 not in properties: #TODO: Skip properties
            #    continue

            #TODO: properties 3 and 4
            if 1 in properties:
                tx, ty, tw, th = anim.sprites[struct.unpack('<I', properties[1])[0]]
            width, height = 1., 1.
            if 2 in properties:
                width, height = struct.unpack('<ff', properties[2])
            width = width_override or width * tw
            height = height_override or height * th
            transform = Matrix.get_scaling_matrix(width, height, 1.)
            if 7 in properties:
                transform = Matrix.get_scaling_matrix(-1., 1., 1.).mult(transform)
            if 9 in properties:
                rx, ry, rz = struct.unpack('<fff', properties[9])
                transform = Matrix.get_rotation_matrix(-rx, 'x').mult(transform)
                transform = Matrix.get_rotation_matrix(ry, 'y').mult(transform)
                transform = Matrix.get_rotation_matrix(-rz, 'z').mult(transform) #TODO: minus, really?
            if 23 in properties: # Reposition
                transform = Matrix.get_translation_matrix(width / 2., height / 2., 0.).mult(transform)

            transform = Matrix.get_translation_matrix(x, y, z).mult(transform)
            vertmat = transform.mult(vertmat)

            uvs = [(tx / anim.size[0],         1. - (ty / anim.size[1])),
                   ((tx + tw) / anim.size[0],  1. - (ty / anim.size[1])),
                   ((tx + tw) / anim.size[0],  1. - ((ty + th) / anim.size[1])),
                   (tx / anim.size[0],         1. - ((ty + th) / anim.size[1]))]

            for i in xrange(4):
                w = vertmat.data[3][i]
                vertices.append((vertmat.data[0][i] / w, vertmat.data[1][i] / w, vertmat.data[2][i] / w))
            faces.append((vertices, uvs))
        objects_faces.append(faces)
    return objects_faces



def objects_faces_to_vertices_uvs(objects):
    vertices = tuple(vertex for obj in objects for face in obj for vertex in face[0]) #TODO: check
    uvs = tuple(uv for obj in objects for face in obj for uv in face[1]) #TODO: check
    return vertices, uvs



def main(path, stage_num):
    # Initialize pygame
    pygame.init()
    window = pygame.display.set_mode((384, 448), pygame.OPENGL | pygame.DOUBLEBUF)

    # Initialize OpenGL
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(30, float(window.get_width())/window.get_height(), 101010101./2010101., 101010101./10101.)

    glHint(GL_FOG_HINT, GL_NICEST)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_FOG)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    # Load data
    with open(path, 'rb') as file:
        archive = PBG3.read(file)
        stage = Stage.read(BytesIO(archive.extract('stage%d.std' % stage_num)))
        anim = Animations.read(BytesIO(archive.extract('stg%dbg.anm' % stage_num)))
        textures_components = [None, None]
        for i, component_name in enumerate((anim.first_name, anim.secondary_name)):
            if component_name:
                textures_components[i] = BytesIO(archive.extract(os.path.basename(component_name)))
        texture = load_texture(*textures_components)

    print(stage.name)

    uvs = []
    vertices = []
    objects_faces = build_objects_faces(stage, anim)
    objects_instances_faces = []
    for obj, ox, oy, oz in stage.object_instances:
        obj_id = stage.objects.index(obj)

        obj_instance = []
        for face_vertices, face_uvs in objects_faces[obj_id]:
            obj_instance.append((tuple((x + ox, y + oy, z + oz) for x, y, z in face_vertices),
                                face_uvs))
        objects_instances_faces.append(obj_instance)

    def keyfunc(obj):
        return min(z for face in obj for x, y, z in face[0])
    objects_instances_faces.sort(key=keyfunc, reverse=True)

    vertices, uvs = objects_faces_to_vertices_uvs(objects_instances_faces)
    nb_vertices = len(vertices)
    vertices_format = 'f' * (3 * nb_vertices)
    uvs_format = 'f' * (2 * nb_vertices)
    vertices, uvs = objects_faces_to_vertices_uvs(objects_instances_faces)
    glVertexPointer(3, GL_FLOAT, 0, struct.pack(vertices_format, *chain(*vertices)))
    glTexCoordPointer(2, GL_FLOAT, 0, struct.pack(uvs_format, *chain(*uvs)))

    x, y, z = 0, 0, 0
    frame = 0
    interpolation = 0, 0, 0
    interpolation2 = 0, 0, 0

    # Main loop
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q)):
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT:
                    pygame.display.toggle_fullscreen()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        for frame_num, message_type, data in stage.script:
            if frame_num == frame and message_type == 1:
                #TODO: move interpolation elsewhere
                next_fog_b, next_fog_g, next_fog_r, _, next_fog_start, next_fog_end = struct.unpack('<BBBBff', data)
            if frame_num == frame and message_type == 3:
                duration, junk1, junk2 = struct.unpack('<III', data)
                interpolation = frame_num, duration, frame_num + duration
                old_unknownx, old_dy, old_dz = unknownx, dy, dz
            if frame_num == frame and message_type == 4:
                duration, junk1, junk2 = struct.unpack('<III', data)
                interpolation2 = frame_num, duration, frame_num + duration
                old_fog_b, old_fog_g, old_fog_r, old_fog_start, old_fog_end = fog_b, fog_g, fog_r, fog_start, fog_end
            if frame_num <= frame and message_type == 0:
                last_message = frame_num, message_type, data
            if frame_num <= frame and message_type == 2:
                next_unknownx, next_dy, next_dz = struct.unpack('<fff', data)
            if frame_num > frame and message_type == 0:
                next_message = frame_num, message_type, data
                break

        if frame < interpolation[2]:
            truc = float(frame - interpolation[0]) / interpolation[1]
            unknownx = old_unknownx + (next_unknownx - old_unknownx) * truc
            dy = old_dy + (next_dy - old_dy) * truc
            dz = old_dz + (next_dz - old_dz) * truc
        else:
            unknownx, dy, dz = next_unknownx, next_dy, next_dz

        if frame < interpolation2[2]:
            truc = float(frame - interpolation2[0]) / interpolation2[1]
            fog_b = old_fog_b + (next_fog_b - old_fog_b) * truc
            fog_g = old_fog_g + (next_fog_g - old_fog_g) * truc
            fog_r = old_fog_r + (next_fog_r - old_fog_r) * truc
            fog_start = old_fog_start + (next_fog_start - old_fog_start) * truc
            fog_end = old_fog_end + (next_fog_end - old_fog_end) * truc
        else:
            fog_r, fog_g, fog_b, fog_start, fog_end = next_fog_r, next_fog_g, next_fog_b, next_fog_start, next_fog_end


        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, fog_start)
        glFogf(GL_FOG_END, fog_end)
        glFogfv(GL_FOG_COLOR, (fog_r / 255., fog_g / 255., fog_b / 255., 1.))


        x1, y1, z1 = struct.unpack('<fff', last_message[2])
        x2, y2, z2 = struct.unpack('<fff', next_message[2])

        truc = (float(frame) - last_message[0]) / (next_message[0] - last_message[0])

        x = x1 + (x2 - x1) * truc
        y = y1 + (y2 - y1) * truc
        z = z1 + (z2 - z1) * truc


        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # Some explanations on the magic constants:
        # 192. = 384. / 2. = width / 2.
        # 224. = 448. / 2. = height / 2.
        # 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
        # This is so that objects on the (O, x, y) plane use pixel coordinates
        gluLookAt(192., 224., - 835.979370 * dz,
                  192., 224. - dy, 750 - 835.979370 * dz, 0., -1., 0.) #TODO: 750 might not be accurate
        #print(glGetFloat(GL_MODELVIEW_MATRIX))
        glTranslatef(-x, -y, -z)

        glDrawArrays(GL_QUADS, 0, nb_vertices)

        #TODO: show the game itself
        # It is displayed on (0, 0, 0), (0, 448, 0), (388, 448, 0), (388, 0, 0)
        # using a camera at (192, 224, -835.979370) looking right behind itself
        # Depth test should be disabled when rendering the game

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

