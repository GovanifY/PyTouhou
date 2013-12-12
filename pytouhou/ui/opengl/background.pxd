from pytouhou.lib.opengl cimport GLuint, GLushort, GLsizei
from .renderer cimport Renderer

cdef struct Vertex:
    float x, y, z
    float u, v
    unsigned char r, g, b, a


cdef class BackgroundRenderer:
    cdef GLuint texture
    cdef GLsizei nb_indices
    cdef unsigned int use_fixed_pipeline

    # For modern GL.
    cdef GLuint vbo, ibo
    cdef GLuint vao

    # For fixed pipeline.
    cdef Vertex *vertex_buffer
    cdef GLushort *indices

    cdef void set_state(self) nogil
    cdef void render_background(self) except *
    cdef void load(self, background, Renderer renderer) except *
