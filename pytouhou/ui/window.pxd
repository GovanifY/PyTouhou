from pytouhou.lib cimport sdl


cdef class Clock:
    cdef unsigned long _ref_tick
    cdef long _target_fps, _ref_frame, _fps_tick, _fps_frame
    cdef double fps

    cdef void set_target_fps(self, long fps) nogil
    cdef void tick(self) nogil except *


cdef class Runner:
    cdef long width, height

    cdef void start(self) except *
    cdef void finish(self) except *
    cdef bint update(self) except *


cdef class Window:
    cdef sdl.Window win
    cdef long fps_limit
    cdef public bint use_fixed_pipeline
    cdef Runner runner
    cdef Clock clock

    cdef void set_size(self, int width, int height) nogil
    cpdef set_runner(self, Runner runner=*)
    cpdef run(self)
    cdef bint run_frame(self) except? False
    cdef double get_fps(self) nogil
