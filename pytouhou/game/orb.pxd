from pytouhou.game.element cimport Element
from pytouhou.game.sprite cimport Sprite
from pytouhou.game.player cimport Player

cdef class Orb(Element):
    cdef public double offset_x, offset_y
    cdef Player player
    cdef object fire

    cpdef update(self)
