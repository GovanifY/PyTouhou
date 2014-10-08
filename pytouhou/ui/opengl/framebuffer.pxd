from pytouhou.lib.opengl cimport GLuint

cdef struct PassthroughVertex:
    short x, y
    float u, v


cdef class Framebuffer:
    cdef GLuint fbo, texture, rbo, vbo, vao
    cdef PassthroughVertex[4] buf

    cpdef bind(self)
    cdef void set_state(self) nogil
    cdef void render(self) nogil
