from pytouhou.game.element cimport Element
from pytouhou.game.sprite cimport Sprite

cdef class Orb(Element):
    cdef public double offset_x, offset_y
    cdef Element player
    cdef object fire

    cpdef update(self)
