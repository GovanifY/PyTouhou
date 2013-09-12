from pytouhou.game.element cimport Element
from pytouhou.game.game cimport Game
from pytouhou.game.player cimport Player
from pytouhou.utils.interpolator cimport Interpolator


cdef class Indicator(Element):
    cdef Item _item

    cdef void update(self) nogil


cdef class Item(Element):
    cdef public object _item_type

    cdef unsigned long frame
    cdef long _type
    cdef double angle, speed
    cdef Game _game
    cdef Player player
    cdef Indicator indicator
    cdef Interpolator speed_interpolator, pos_interpolator

    cdef void autocollect(self, Player player) except *
    cdef void on_collect(self, Player player) except *
    cpdef update(self)
