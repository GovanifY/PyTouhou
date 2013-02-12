cdef struct Vertex:
    int x, y, z
    float u, v
    unsigned char r, g, b, a


cdef struct VertexFloat:
    float x, y, z
    float u, v
    unsigned char r, g, b, a


cdef class Renderer:
    cdef public texture_manager
    cdef Vertex *vertex_buffer
    cdef object texture_key
    cdef unsigned short blendfunc, nb_vertices
    cdef VertexFloat *background_vertex_buffer

    cpdef render_elements(self, elements)
    cpdef render_background(self)
    cpdef prerender_background(self, background)
    cpdef ortho_2d(self, left, right, bottom, top)
    cpdef look_at(self, eye, center, up)
    cpdef perspective(self, fovy, aspect, zNear, zFar)
    cpdef setup_camera(self, dx, dy, dz)
