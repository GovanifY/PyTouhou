cdef class BitStream:
    cdef public object io
    cdef unsigned int bits
    cdef unsigned char byte

    cdef bint read_bit(self) except -1
    cpdef unsigned int read(self, unsigned int nb_bits) except? 4242
    cpdef write_bit(self, bint bit)
    cpdef write(self, unsigned int bits, unsigned int nb_bits)
    cpdef flush(self)
