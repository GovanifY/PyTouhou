from pytouhou.lib.sdl cimport Font
from pytouhou.lib.sdl cimport Surface, Window

cdef class TextureManager:
    cdef object loader
    cdef Window window

    cdef bint load(self, dict anms) except True
    cdef load_texture(self, Surface texture)

cdef class FontManager:
    cdef Font font
    cdef Window window

    cdef bint load(self, dict labels) except True
