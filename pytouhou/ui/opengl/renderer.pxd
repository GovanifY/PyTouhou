from cpython cimport PyObject
from pytouhou.lib.opengl cimport GLuint
from .texture cimport TextureManager, FontManager

cdef struct Vertex:
    short x, y, z, padding
    float u, v
    unsigned char r, g, b, a


cdef struct PassthroughVertex:
    short x, y
    float u, v


cdef class Texture:
    cdef long key
    cdef GLuint texture
    cdef GLuint *pointer
    cdef unsigned short indices[2][65536]

    #XXX: keep a reference so that when __dealloc__ is called self.pointer is still valid.
    cdef Renderer renderer


cdef class Renderer:
    cdef TextureManager texture_manager
    cdef FontManager font_manager
    cdef Vertex vertex_buffer[MAX_ELEMENTS]
    cdef long x, y, width, height

    # For modern GL.
    cdef GLuint vbo, framebuffer_vbo, framebuffer_ibo
    cdef GLuint vao, framebuffer_vao

    cdef GLuint textures[MAX_TEXTURES]
    cdef unsigned short *indices[MAX_TEXTURES][2]
    cdef unsigned short last_indices[2 * MAX_TEXTURES]
    cdef PyObject *elements[640*3]

    cdef void set_state(self) nogil
    cdef void render_elements(self, elements) except *
    cdef void render_quads(self, rects, colors, GLuint texture) except *

    cdef void set_framebuffer_state(self) nogil
    cdef void render_framebuffer(self, Framebuffer fb) except *


cdef class Framebuffer:
    cdef GLuint fbo, texture, rbo
    cdef int x, y, width, height

    cpdef bind(self)
