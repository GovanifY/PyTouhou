from pytouhou.lib.opengl cimport GLuint

cdef struct PassthroughVertex:
    short x, y
    float u, v


cdef class Framebuffer:
    cdef GLuint fbo, texture, rbo, vbo, vao
    cdef PassthroughVertex[4] buf
    cdef int x, y, width, height

    cpdef bind(self)
    cdef void set_state(self) nogil
    cdef void render(self, int x, int y, int width, int height) nogil
