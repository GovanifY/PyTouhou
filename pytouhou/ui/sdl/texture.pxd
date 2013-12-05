#from pytouhou.lib.sdl cimport Font
from pytouhou.lib.sdl cimport Surface, Window

cdef class TextureManager:
    cdef object loader
    cdef Window window

    cdef void load(self, dict anms) except *
    cdef load_texture(self, Surface texture)

#cdef class FontManager:
#    cdef Font font
#    cdef object renderer, texture_class
#
#    cdef load(self, list labels)
