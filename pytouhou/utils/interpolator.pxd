cdef class Interpolator:
    cdef unsigned long start_frame, end_frame, _frame
    cdef long _length
    cdef double *_values, *start_values, *end_values
    cdef object _formula

    cpdef set_interpolation_start(self, unsigned long frame, tuple values)
    cpdef set_interpolation_end(self, unsigned long frame, tuple values)
    cpdef set_interpolation_end_frame(self, unsigned long end_frame)
    cpdef set_interpolation_end_values(self, tuple values)
    cpdef update(self, unsigned long frame)
