cdef struct Vertex:
    int x, y, z
    float u, v
    unsigned char r, g, b, a


cdef class Renderer:
    cdef public texture_manager
    cdef unsigned int vbo
    cdef Vertex *vertex_buffer

    cpdef render_elements(self, elements)
