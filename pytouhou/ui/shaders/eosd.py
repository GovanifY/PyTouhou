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

            uniform mat4 mvp;

            void main()
            {
                gl_Position = mvp * gl_Vertex;
                gl_FrontColor = gl_Color;
                gl_TexCoord[0] = gl_MultiTexCoord0;
            }
        '''], [ '''
            #version 120

            uniform sampler2D color_map;

            void main()
            {
                gl_FragColor = texture2D(color_map, gl_TexCoord[0].st) * gl_Color;
            }
        '''])


class BackgroundShader(Shader):
    def __init__(self):
        Shader.__init__(self, ['''
            #version 120

            uniform mat4 model_view;
            uniform mat4 projection;

            varying float fog_density;

            void main()
            {
                gl_Position = model_view * gl_Vertex;
                gl_FrontColor = gl_Color;
                gl_TexCoord[0] = gl_MultiTexCoord0;

                float fog_position = -gl_Position.z / gl_Position.w;
                fog_density = clamp((gl_Fog.end - fog_position) * gl_Fog.scale, 0.0f, 1.0f);

                gl_Position = projection * gl_Position;
            }
        '''], [ '''
            #version 120

            uniform sampler2D color_map;

            varying float fog_density;

            void main()
            {
                vec4 color = texture2D(color_map, gl_TexCoord[0].st) * gl_Color;
                gl_FragColor = mix(gl_Fog.color, color, fog_density);
                gl_FragColor.w = color.w;
            }
        '''])
