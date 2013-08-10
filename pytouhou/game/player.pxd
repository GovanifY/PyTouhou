from pytouhou.game.element cimport Element
from pytouhou.game.game cimport Game

cdef class PlayerState:
    cdef public double x, y
    cdef public bint touchable, focused
    cdef public long character, score, effective_score, lives, bombs, power, graze, points, invulnerable_time, power_bonus


cdef class Player(Element):
    cdef public PlayerState state
    cdef public long death_time
    cdef public Game _game

    cdef object anm
    cdef tuple speeds
    cdef long fire_time, bomb_time, direction

    cdef void set_anim(self, index)
    cpdef play_sound(self, str name)
    cpdef collide(self)
    cdef void fire(self)
    cpdef update(self, long keystate)
