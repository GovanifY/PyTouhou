cdef class Matrix:
    cdef public list data

    cpdef flip(Matrix self)
    cpdef scale(Matrix self, x, y, z)
    cpdef scale2d(Matrix self, x, y)
    cpdef translate(Matrix self, x, y, z)
    cpdef rotate_x(Matrix self, angle)
    cpdef rotate_y(Matrix self, angle)
    cpdef rotate_z(Matrix self, angle)
