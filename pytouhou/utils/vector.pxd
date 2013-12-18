cdef struct Vector:
    float x, y, z

cdef Vector sub(Vector vec1, Vector vec2)
cdef Vector cross(Vector vec1, Vector vec2)
cdef float dot(Vector vec1, Vector vec2) nogil
cdef Vector normalize(Vector vec)
