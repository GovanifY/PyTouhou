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

cimport cython

cimport pytouhou.lib.sdl as sdl


cdef class Clock:
    def __init__(self, long fps=-1):
        self._target_fps = 0
        self._ref_tick = 0
        self._ref_frame = 0
        self._fps_tick = 0
        self._fps_frame = 0
        self.fps = 0
        self.set_target_fps(fps)


    cdef void set_target_fps(self, long fps) nogil:
        self._target_fps = fps
        self._ref_tick = 0
        self._fps_tick = 0


    @cython.cdivision(True)
    cdef bint tick(self) nogil except True:
        current = sdl.get_ticks()

        if not self._ref_tick:
            self._ref_tick = current
            self._ref_frame = 0

        if self._fps_frame >= (self._target_fps if self._target_fps > 0 else 60):
            self.fps = self._fps_frame * 1000. / (current - self._fps_tick)
            self._fps_tick = current
            self._fps_frame = 0
            # If we are relying on vsync, but vsync doesn't work or is higher
            # than 60 fps, limit ourselves to 60 fps.
            if self._target_fps < 0 and self.fps > 64.:
                self._target_fps = 60

        self._ref_frame += 1
        self._fps_frame += 1

        target_tick = self._ref_tick
        if self._target_fps > 0:
            target_tick += <unsigned long>(self._ref_frame * 1000 / self._target_fps)

        if current <= target_tick:
            sdl.delay(target_tick - current)
        else:
            self._ref_tick = current
            self._ref_frame = 0



cdef class Runner:
    cdef bint start(self) except True:
        pass

    cdef bint finish(self) except True:
        pass

    cpdef bint update(self, bint render) except -1:
        return False



cdef class Window:
    def __init__(self, backend, int width=640, int height=480, long fps_limit=-1, frameskip=1):
        if backend is not None:
            self.win = backend.create_window(
                'PyTouhou',
                sdl.WINDOWPOS_CENTERED, sdl.WINDOWPOS_CENTERED,
                width, height,
                frameskip)

        self.clock = Clock(fps_limit)
        self.frame = 0
        self.frameskip = frameskip
        self.width = width
        self.height = height


    cdef void set_size(self, int width, int height) nogil:
        self.win.set_window_size(width, height)


    cpdef set_runner(self, Runner runner=None):
        self.runner = runner
        if runner is not None:
            runner.start()


    cpdef run(self):
        try:
            while self.run_frame():
                pass
        finally:
            if self.runner is not None:
                self.runner.finish()


    @cython.cdivision(True)
    cdef bint run_frame(self) except -1:
        cdef bint render = (self.win is not None and
                            (self.frameskip <= 1 or not self.frame % self.frameskip))

        running = False
        if self.runner is not None:
            running = self.runner.update(render)
        if render:
            self.win.present()

        self.clock.tick()
        self.frame += 1

        return running


    cdef double get_fps(self) nogil:
        return self.clock.fps


    cdef list get_events(self):
        return self.win.get_events()


    cdef int get_keystate(self) nogil:
        return self.win.get_keystate()


    cdef void toggle_fullscreen(self) nogil:
        self.win.toggle_fullscreen()
