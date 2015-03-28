from pytouhou.lib.opengl cimport GLuint
from pytouhou.utils.matrix cimport Matrix
from .shader cimport Shader

cdef struct PassthroughVertex:
    short x, y
    float u, v


cdef class Framebuffer:
    cdef GLuint fbo, texture, rbo

    # Used by the use_framebuffer_blit path
    cdef int x, y, width, height

    # Used by the other one.
    cdef GLuint vbo, vao
    cdef Shader shader
    cdef Matrix *mvp
    cdef PassthroughVertex[4] buf

    cpdef bind(self)
    cdef void set_state(self) nogil
    cdef bint render(self, int x, int y, int width, int height) except True
