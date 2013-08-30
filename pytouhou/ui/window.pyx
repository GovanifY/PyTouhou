# -*- encoding: utf-8 -*-
##
## Copyright (C) 2013 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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


from pytouhou.lib import sdl

from pytouhou.lib.opengl cimport \
         (glEnable, glHint, glEnableClientState, GL_TEXTURE_2D, GL_BLEND,
          GL_PERSPECTIVE_CORRECTION_HINT, GL_FOG_HINT, GL_NICEST,
          GL_COLOR_ARRAY, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY)

IF USE_GLEW:
    from pytouhou.lib.opengl cimport glewInit


class Clock:
    def __init__(self, fps=None):
        self._target_fps = 0
        self._ref_tick = 0
        self._ref_frame = 0
        self._fps_tick = 0
        self._fps_frame = 0
        self._rate = 0
        self.set_target_fps(fps)


    def set_target_fps(self, fps):
        self._target_fps = fps
        self._ref_tick = 0
        self._fps_tick = 0


    def get_fps(self):
        return self._rate


    def tick(self):
        current = sdl.get_ticks()

        if not self._ref_tick:
            self._ref_tick = current
            self._ref_frame = 0

        if self._fps_frame >= (self._target_fps if self._target_fps > 0 else 60):
            self._rate = self._fps_frame * 1000. / (current - self._fps_tick)
            self._fps_tick = current
            self._fps_frame = 0
            # If we are relying on vsync, but vsync doesn't work or is higher
            # than 60 fps, limit ourselves to 60 fps.
            if self._target_fps < 0 and self._rate > 64.:
                self._target_fps = 60

        self._ref_frame += 1
        self._fps_frame += 1

        target_tick = self._ref_tick
        if self._target_fps:
            target_tick += int(self._ref_frame * 1000 / self._target_fps)

        if current <= target_tick:
            sdl.delay(target_tick - current)
        else:
            self._ref_tick = current
            self._ref_frame = 0



class Window(object):
    def __init__(self, size=None, double_buffer=True, fps_limit=60,
                 fixed_pipeline=False, sound=True):
        self.fps_limit = fps_limit
        self.use_fixed_pipeline = fixed_pipeline
        self.runner = None

        IF UNAME_SYSNAME == "Windows":
            sdl.set_main_ready()
        sdl.init(sdl.INIT_VIDEO)
        sdl.img_init(sdl.INIT_PNG)
        if sound:
            sdl.mix_init(0)

        sdl.gl_set_attribute(sdl.GL_CONTEXT_MAJOR_VERSION, 2)
        sdl.gl_set_attribute(sdl.GL_CONTEXT_MINOR_VERSION, 1)
        sdl.gl_set_attribute(sdl.GL_DOUBLEBUFFER, int(double_buffer))
        sdl.gl_set_attribute(sdl.GL_DEPTH_SIZE, 24)

        self.width, self.height = size if size else (640, 480)

        self.win = sdl.Window('PyTouhou',
                              sdl.WINDOWPOS_CENTERED, sdl.WINDOWPOS_CENTERED,
                              self.width, self.height,
                              sdl.WINDOW_OPENGL | sdl.WINDOW_SHOWN)
        self.win.gl_create_context()

        IF USE_GLEW:
            if glewInit() != 0:
                raise Exception('GLEW init fail!')

        # Initialize OpenGL
        glEnable(GL_BLEND)
        if self.use_fixed_pipeline:
            glEnable(GL_TEXTURE_2D)
            glHint(GL_FOG_HINT, GL_NICEST)
            glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
            glEnableClientState(GL_COLOR_ARRAY)
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        # Initialize sound
        if sound:
            sdl.mix_open_audio(44100, sdl.DEFAULT_FORMAT, 2, 4096)
            sdl.mix_allocate_channels(26) #TODO: make it dependent on the SFX number.

        self.clock = Clock(self.fps_limit)


    def set_size(self, width, height):
        self.win.set_window_size(width, height)


    def set_runner(self, runner):
        self.runner = runner
        runner.start()


    def run(self):
        try:
            while self.run_frame():
                pass
        finally:
            self.runner.finish()


    def run_frame(self):
        if self.runner:
            running = self.runner.update()
        self.win.gl_swap_window()
        self.clock.tick()
        return running


    def __dealloc__(self):
        self.win.gl_delete_context()
        self.win.destroy_window()
        sdl.mix_close_audio()
        sdl.mix_quit()
        sdl.img_quit()
        sdl.quit()
