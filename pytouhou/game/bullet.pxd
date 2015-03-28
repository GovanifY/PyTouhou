from pytouhou.game.element cimport Element
from pytouhou.game.game cimport Game
from pytouhou.game.bullettype cimport BulletType
from pytouhou.utils.interpolator cimport Interpolator


cdef enum State:
    LAUNCHING, LAUNCHED, CANCELLED


cdef class Bullet(Element):
    cdef public State state
    cdef public unsigned long flags, frame, sprite_idx_offset, damage
    cdef public double dx, dy, angle, speed
    cdef public bint was_visible, grazed
    cdef public Element target
    cdef public BulletType _bullet_type
    cdef public list attributes

    cdef double hitbox[2]
    cdef Interpolator speed_interpolator
    cdef Game _game
    cdef long player

    cdef bint is_visible(self, unsigned int screen_width, unsigned int screen_height) nogil
    cpdef set_anim(self, sprite_idx_offset=*)
    cdef bint launch(self) except True
    cdef bint collide(self) except True
    cdef bint cancel(self) except True
    cdef bint update(self) except True
