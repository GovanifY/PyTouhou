# Events
EXIT = 1
PAUSE = 2
SCREENSHOT = 3
RESIZE = 4
FULLSCREEN = 5
DOWN = 6

# Possible keystates.
SHOOT = 1
BOMB = 2
FOCUS = 4
# ??
UP = 16
DOWN = 32
LEFT = 64
RIGHT = 128
SKIP = 256


class Error(Exception):
    pass


cdef class Window:
    cdef void create_gl_context(self) except *:
        pass

    cdef void present(self) nogil:
        pass

    cdef void set_window_size(self, int width, int height) nogil:
        pass

    cdef void set_swap_interval(self, int interval) except *:
        pass

    cdef list get_events(self):
        return []

    cdef int get_keystate(self) nogil:
        return 0

    cdef void toggle_fullscreen(self) nogil:
        pass
