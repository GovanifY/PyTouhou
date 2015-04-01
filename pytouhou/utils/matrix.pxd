ctypedef struct Matrix:
    float a, b, c, d
    float e, f, g, h
    float i, j, k, l
    float m, n, o, p

cdef Matrix *new_matrix(Matrix *data) nogil
cdef Matrix *new_identity() nogil

cdef void mul(Matrix *mat1, Matrix *mat2) nogil
cdef void flip(Matrix *mat) nogil
cdef void scale2d(Matrix *mat, float x, float y) nogil
cdef void translate(Matrix *mat, float[3] offset) nogil
cdef void translate2d(Matrix *mat, float x, float y) nogil
cdef void rotate_x(Matrix *mat, float angle) nogil
cdef void rotate_y(Matrix *mat, float angle) nogil
cdef void rotate_z(Matrix *mat, float angle) nogil
