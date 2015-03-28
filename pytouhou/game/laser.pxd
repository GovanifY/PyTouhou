from pytouhou.game.element cimport Element
from pytouhou.game.sprite cimport Sprite
from pytouhou.game.lasertype cimport LaserType

cdef enum State:
    STARTING, STARTED, STOPPING


cdef class LaserLaunchAnim(Element):
    cdef Laser _laser

    cpdef update(self)


cdef class Laser(Element):
    cdef public unsigned long frame
    cdef public double angle

    cdef unsigned long start_duration, duration, stop_duration, grazing_delay,
    cdef unsigned long grazing_extra_duration, sprite_idx_offset
    cdef double base_pos[2]
    cdef double speed, start_offset, end_offset, max_length, width
    cdef State state
    cdef LaserType _laser_type

    cdef bint set_anim(self, long sprite_idx_offset=*) except True
    cpdef set_base_pos(self, double x, double y)
    cdef bint _check_collision(self, double point[2], double border_size)
    cdef bint check_collision(self, double point[2])
    cdef bint check_grazing(self, double point[2])
    #def get_bullets_pos(self)
    cpdef cancel(self)
    cpdef update(self)


cdef class PlayerLaser(Element):
    cdef double hitbox[2]
    cdef double angle, offset
    cdef unsigned long frame, duration, sprite_idx_offset, damage
    cdef Element origin
    cdef LaserType _laser_type

    cdef bint set_anim(self, long sprite_idx_offset=*) except True
    cdef bint cancel(self) except True
    cdef bint update(self) except True
