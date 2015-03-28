from pytouhou.lib cimport sdl


cdef class Clock:
    cdef unsigned long _ref_tick
    cdef long _target_fps, _ref_frame, _fps_tick, _fps_frame
    cdef double fps

    cdef void set_target_fps(self, long fps) nogil
    cdef bint tick(self) nogil except True


cdef class Runner:
    cdef long width, height

    cdef bint start(self) except True
    cdef bint finish(self) except True
    cpdef bint update(self, bint render) except -1


cdef class Window:
    cdef sdl.Window win
    cdef Runner runner
    cdef Clock clock
    cdef int frame, frameskip
    cdef int width, height

    cdef void set_size(self, int width, int height) nogil
    cpdef set_runner(self, Runner runner=*)
    cpdef run(self)
    cdef bint run_frame(self) except -1
    cdef double get_fps(self) nogil
