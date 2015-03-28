from pytouhou.game.element cimport Element
from pytouhou.game.sprite cimport Sprite
from pytouhou.utils.interpolator cimport Interpolator

cdef class Glyph(Element):
    pass


cdef class Widget(Element):
    cdef public object update
    cdef public bint changed

    cdef unsigned long frame
    cdef object back_anm

    #def update(self)


cdef class GlyphCollection(Widget):
    cdef Sprite ref_sprite
    cdef object anm
    cdef list glyphes
    cdef long xspacing

    cpdef set_length(self, unsigned long length)
    cpdef set_sprites(self, list sprite_indexes)
    cpdef set_color(self, text=*, color=*)
    cpdef set_alpha(self, unsigned char alpha)


cdef class Text(GlyphCollection):
    cdef bytes text
    cdef unsigned long timeout, duration, start
    cdef long shift
    cdef Interpolator fade_interpolator
    cdef unsigned char alpha

    cpdef set_text(self, text)
    #def timeout_update(self)
    #def move_timeout_update(self)
    #def fadeout_timeout_update(self)
    cdef bint fade(self, unsigned long duration, unsigned char alpha, formula=*) except True
    cpdef set_timeout(self, unsigned long timeout, str effect=*, unsigned long duration=*, unsigned long start=*)


cdef class Counter(GlyphCollection):
    cdef long value

    cpdef set_value(self, long value)


cdef class Gauge(Element):
    cdef public long value, max_length, maximum

    cpdef set_value(self, long value)
    cpdef update(self)


cdef class NativeText(Element):
    cdef public object update

    cdef unicode text
    cdef str align #TODO: use a proper enum.
    cdef unsigned long frame, timeout, duration, start
    cdef double to[2]
    cdef double end[2]
    cdef list gradient
    cdef Interpolator fade_interpolator, offset_interpolator

    #XXX
    cdef public bint shadow
    cdef public long width, height
    cdef public unsigned char alpha
    cdef public object texture

    #def normal_update(self)
    #def timeout_update(self)
    #def move_timeout_update(self)
    #def move_ex_timeout_update(self)
    #def fadeout_timeout_update(self)

    cdef bint fade(self, unsigned long duration, unsigned char alpha, formula=*) except True
    cdef bint move_in(self, unsigned long duration, double x, double y, formula=*) except True
    cpdef set_timeout(self, unsigned long timeout, str effect=*, unsigned long duration=*, unsigned long start=*, to=*, end=*)
