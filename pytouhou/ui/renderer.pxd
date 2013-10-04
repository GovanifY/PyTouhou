from cpython cimport PyObject
from pytouhou.lib.opengl cimport GLuint

cdef struct Vertex:
    int x, y, z
    float u, v
    unsigned char r, g, b, a


cdef struct PassthroughVertex:
    int x, y
    float u, v


cdef class Renderer:
    cdef public texture_manager, font_manager
    cdef GLuint vbo, framebuffer_vbo
    cdef Vertex *vertex_buffer
    cdef long x, y, width, height

    cdef bint use_fixed_pipeline #XXX

    cdef unsigned short *indices[2][MAX_TEXTURES]
    cdef unsigned short last_indices[2 * MAX_TEXTURES]
    cdef PyObject *elements[640*3]

    cdef void render_elements(self, elements) except *
    cdef void render_quads(self, rects, colors, texture) except *
    cdef void render_framebuffer(self, Framebuffer fb) except *


cdef class Framebuffer:
    cdef GLuint fbo, texture, rbo
    cdef int x, y, width, height

    cpdef bind(self)
