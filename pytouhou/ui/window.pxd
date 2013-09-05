from pytouhou.lib cimport sdl


cdef class Clock:
    cdef long _target_fps, _ref_tick, _ref_frame, _fps_tick, _fps_frame
    cdef double _rate

    cdef void set_target_fps(self, long fps) nogil
    cdef double get_fps(self) nogil
    cdef void tick(self) nogil except *


cdef class Window:
    cdef sdl.Window win
    cdef long fps_limit
    cdef public long width, height
    cdef public bint use_fixed_pipeline
    cdef object runner
    cdef Clock clock

    cdef void set_size(self, int width, int height) nogil
    cpdef set_runner(self, runner=*)
    cpdef run(self)
    cdef bint run_frame(self) except? False
    cpdef double get_fps(self)
