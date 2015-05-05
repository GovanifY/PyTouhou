from pytouhou.game.effect cimport Effect
from pytouhou.utils.interpolator cimport Interpolator

cdef class Particle(Effect):
    cdef long frame, duration
    cdef Interpolator pos_interpolator

    cpdef update(self)
