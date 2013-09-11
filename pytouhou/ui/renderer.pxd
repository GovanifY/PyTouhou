from cpython cimport PyObject
from .window cimport Window
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

    cdef bint use_fixed_pipeline #XXX

    cdef unsigned short *indices[2][MAX_TEXTURES]
    cdef unsigned short last_indices[2 * MAX_TEXTURES]
    cdef PyObject *elements[640*3]

    cpdef render_elements(self, elements)
    cpdef render_quads(self, rects, colors, texture)
    cpdef render_framebuffer(self, Framebuffer fb, Window window)


cdef class Framebuffer:
    cdef GLuint fbo, texture, rbo
    cdef int x, y, width, height

    cpdef bind(self)
