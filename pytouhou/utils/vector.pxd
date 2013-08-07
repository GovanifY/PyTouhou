cdef class Vector:
    cdef float x, y, z

    cdef Vector sub(self, Vector other)

cdef Vector cross(Vector vec1, Vector vec2)
cdef float dot(Vector vec1, Vector vec2)
cdef Vector normalize(Vector vec)
