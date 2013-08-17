from pytouhou.game.element cimport Element
from pytouhou.utils.interpolator cimport Interpolator

cdef class Effect(Element):
    cpdef update(self)


cdef class Particle(Effect):
    cdef long frame, duration
    cdef Interpolator pos_interpolator

    cpdef update(self)
