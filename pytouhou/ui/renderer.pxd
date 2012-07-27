cdef struct Vertex:
    int x, y, z
    float u, v
    unsigned char r, g, b, a


cdef class Renderer:
    cdef public texture_manager
    cdef Vertex *vertex_buffer

    cpdef render_elements(self, elements)
    cpdef ortho_2d(self, left, right, bottom, top)
    cpdef look_at(self, eye, center, up)
    cpdef perspective(self, fovy, aspect, zNear, zFar)
    cpdef setup_camera(self, dx, dy, dz)
