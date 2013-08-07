cdef class Matrix:
    cdef float data[16]

    cdef void flip(self) nogil
    cdef void scale(self, float x, float y, float z) nogil
    cdef void scale2d(self, float x, float y) nogil
    cdef void translate(self, float x, float y, float z) nogil
    cdef void rotate_x(self, float angle) nogil
    cdef void rotate_y(self, float angle) nogil
    cdef void rotate_z(self, float angle) nogil
