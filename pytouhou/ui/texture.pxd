from pytouhou.lib.sdl cimport Font

cdef class TextureManager:
    cdef object loader, renderer, texture_class

    cdef void load(self, dict anms) except *

cdef class FontManager:
    cdef Font font
    cdef object renderer, texture_class

    cdef void load(self, list labels) except *
