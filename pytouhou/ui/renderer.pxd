from cpython cimport PyObject

cdef struct Vertex:
    int x, y, z
    float u, v
    unsigned char r, g, b, a


cdef class Renderer:
    cdef public texture_manager
    cdef unsigned int vbo
    cdef Vertex *vertex_buffer

    cdef unsigned short *indices[2][MAX_TEXTURES]
    cdef unsigned short last_indices[2 * MAX_TEXTURES]
    cdef PyObject *elements[640*3]

    cpdef render_elements(self, elements)
    cpdef render_quads(self, rects, colors, texture)
