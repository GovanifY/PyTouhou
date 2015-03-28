from pytouhou.lib.sdl cimport Font

cdef class TextureManager:
    cdef object loader, renderer, texture_class

    cdef bint load(self, dict anms) except True

cdef class FontManager:
    cdef Font font
    cdef object renderer, texture_class

    cdef bint load(self, dict labels) except True
