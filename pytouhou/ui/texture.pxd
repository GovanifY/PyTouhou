from pytouhou.lib.sdl cimport Font

cdef class TextureManager:
    cdef object loader, renderer, texture_class

    cdef load(self, dict anms)

cdef class FontManager:
    cdef Font font
    cdef object renderer, texture_class

    cdef load(self, list labels)
