cdef class Random:
    cdef unsigned short seed
    cdef unsigned long counter

    cdef void set_seed(self, unsigned short seed) nogil
    cdef unsigned short rewind(self) nogil

    cpdef unsigned short rand_uint16(self)
    cpdef unsigned int rand_uint32(self)
    cpdef double rand_double(self)
