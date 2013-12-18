from .matrix cimport Matrix

cdef Matrix *ortho_2d(float left, float right, float bottom, float top) nogil
cdef Matrix *perspective(float fovy, float aspect, float zNear, float zFar) nogil
cdef Matrix *setup_camera(float dx, float dy, float dz)
