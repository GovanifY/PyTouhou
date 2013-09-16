from pytouhou.game.element cimport Element
from pytouhou.game.sprite cimport Sprite
from pytouhou.game.player cimport PlayerState

cdef class Orb(Element):
    cdef public double offset_x, offset_y
    cdef PlayerState player_state
    cdef object fire

    cpdef update(self)
