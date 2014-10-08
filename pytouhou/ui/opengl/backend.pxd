from pytouhou.lib.sdl cimport SDL_GLprofile

cdef SDL_GLprofile profile
cdef int major
cdef int minor
cdef int double_buffer
cdef bint is_legacy
cdef bint use_debug_group
cdef bint use_vao
cdef bint use_primitive_restart
cdef str shader_header
