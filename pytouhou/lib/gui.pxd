# Events
cdef int EXIT
cdef int PAUSE
cdef int SCREENSHOT
cdef int RESIZE
cdef int FULLSCREEN
cdef int DOWN

# Keystates
cdef int SHOOT
cdef int BOMB
cdef int FOCUS
# ??
cdef int UP
cdef int DOWN
cdef int LEFT
cdef int RIGHT
cdef int SKIP


cdef class Window:
    cdef void create_gl_context(self) except *
    cdef void present(self) nogil
    cdef void set_window_size(self, int width, int height) nogil
    cdef void set_swap_interval(self, int interval) except *
    cdef list get_events(self)
    cdef int get_keystate(self) nogil
    cdef void toggle_fullscreen(self) nogil
