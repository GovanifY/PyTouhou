from pytouhou.lib.sdl cimport SDL_GLprofile

cdef SDL_GLprofile flavor
cdef str version
cdef int major
cdef int minor
cdef int double_buffer
cdef bint is_legacy
cdef str shader_header
