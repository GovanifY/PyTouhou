from pytouhou.lib.opengl cimport GLenum_mode

cdef bint use_glfw
cdef str profile
cdef int major
cdef int minor
cdef int double_buffer
cdef bint is_legacy
cdef GLenum_mode primitive_mode
cdef bint use_debug_group
cdef bint use_vao
cdef bint use_framebuffer_blit
cdef bint use_primitive_restart
cdef bint use_pack_invert
cdef bint use_scaled_rendering
cdef bytes shader_header
