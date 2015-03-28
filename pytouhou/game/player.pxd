from pytouhou.game.element cimport Element
from pytouhou.game.game cimport Game

cdef class Player(Element):
    cdef public Game _game
    cdef public long death_time
    cdef public bint touchable, focused
    cdef public long character, score, effective_score, lives, bombs, power
    cdef public long graze, points

    cdef long number
    cdef long invulnerable_time, power_bonus, continues, continues_used, miss,
    cdef long bombs_used

    cdef object anm
    cdef tuple speeds
    cdef long fire_time, bomb_time, direction

    cdef bint set_anim(self, index) except True
    cdef bint play_sound(self, str name) except True
    cdef bint collide(self) except True
    cdef bint fire(self) except True
    cpdef update(self, long keystate)
