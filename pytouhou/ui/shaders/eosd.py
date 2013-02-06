# -*- encoding: utf-8 -*-
##
## Copyright (C) 2012 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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


from pytouhou.ui.shader import Shader


class GameShader(Shader):
    def __init__(self):
        Shader.__init__(self, ['''
            #version 120

            attribute vec3 in_position;
            attribute vec2 in_texcoord;
            attribute vec4 in_color;

            uniform mat4 mvp;

            varying vec2 texcoord;
            varying vec4 color;

            void main()
            {
                gl_Position = mvp * vec4(in_position, 1.0);
                texcoord = in_texcoord;
                color = in_color;
            }
        '''], ['''
            #version 120

            varying vec2 texcoord;
            varying vec4 color;

            uniform sampler2D color_map;

            void main()
            {
                gl_FragColor = texture2D(color_map, texcoord) * color;
            }
        '''])


class BackgroundShader(Shader):
    def __init__(self):
        Shader.__init__(self, ['''
            #version 120

            attribute vec3 in_position;
            attribute vec2 in_texcoord;
            attribute vec4 in_color;

            uniform mat4 model_view;
            uniform mat4 projection;

            varying vec2 texcoord;
            varying vec4 color;
            varying float fog_density;

            void main()
            {
                vec4 position = model_view * vec4(in_position, 1.0);
                texcoord = in_texcoord;
                color = in_color;

                float fog_position = -position.z / position.w;
                fog_density = clamp((gl_Fog.end - fog_position) * gl_Fog.scale, 0.0f, 1.0f);

                gl_Position = projection * position;
            }
        '''], ['''
            #version 120

            varying vec2 texcoord;
            varying vec4 color;
            varying float fog_density;

            uniform sampler2D color_map;

            void main()
            {
                vec4 temp_color = texture2D(color_map, texcoord) * color;
                gl_FragColor = mix(gl_Fog.color, temp_color, fog_density);
                gl_FragColor.a = temp_color.a;
            }
        '''])
