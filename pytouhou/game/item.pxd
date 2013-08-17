from pytouhou.game.element cimport Element
from pytouhou.game.player cimport Player
from pytouhou.utils.interpolator cimport Interpolator


cdef class Indicator(Element):
    cdef Item _item

    cpdef update(self)


cdef class Item(Element):
    cdef public object _item_type

    cdef object _game
    cdef unsigned long frame
    cdef long _type
    cdef double angle, speed
    cdef Player player
    cdef Indicator indicator
    cdef Interpolator speed_interpolator, pos_interpolator

    cpdef autocollect(self, Player player)
    cpdef on_collect(self, Player player)
    cpdef update(self)
