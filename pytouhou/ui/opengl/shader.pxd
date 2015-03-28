from pytouhou.lib.opengl cimport GLuint, GLint, GLchar, GLenum_shader, GLfloat
from pytouhou.utils.matrix cimport Matrix

cdef class Shader:
    cdef GLuint handle
    cdef bint linked
    cdef dict location_cache

    cdef bint create_shader(self, const GLchar *string, GLenum_shader shader_type) except True
    cdef bint link(self) except True
    cdef GLint get_uniform_location(self, name) except -1
    cdef void bind(self) nogil
    cdef bint uniform_1(self, name, GLfloat val) except True
    cdef bint uniform_4(self, name, GLfloat a, GLfloat b, GLfloat c, GLfloat d) except True
    cdef bint uniform_matrix(self, name, Matrix *mat) except True
