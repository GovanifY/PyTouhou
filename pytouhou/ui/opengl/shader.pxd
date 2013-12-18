from pytouhou.lib.opengl cimport GLuint, GLint, GLchar, GLenum, GLfloat
from pytouhou.utils.matrix cimport Matrix

cdef class Shader:
    cdef GLuint handle
    cdef bint linked
    cdef dict location_cache

    cdef void create_shader(self, const GLchar *string, GLenum shader_type) except *
    cdef void link(self) except *
    cdef GLint get_uniform_location(self, name) except -1
    cdef void bind(self) nogil
    cdef void uniform_1(self, name, GLfloat val) except *
    cdef void uniform_4(self, name, GLfloat a, GLfloat b, GLfloat c, GLfloat d) except *
    cdef void uniform_matrix(self, name, Matrix *mat) except *
