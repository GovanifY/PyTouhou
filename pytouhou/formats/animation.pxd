cdef class Animation:
    cdef public long version
    cdef public unicode first_name, secondary_name
    cdef public dict sprites, scripts
    cdef public object texture

    cdef double size_inv[2]
