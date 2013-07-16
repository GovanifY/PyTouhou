cdef float* matrix_to_floats(Matrix self)

cdef class Matrix:
    cdef public list data
    cdef float *c_data

    cpdef flip(self)
    cpdef scale(self, x, y, z)
    cpdef scale2d(self, x, y)
    cpdef translate(self, x, y, z)
    cpdef rotate_x(self, angle)
    cpdef rotate_y(self, angle)
    cpdef rotate_z(self, angle)
