from pytouhou.utils.interpolator cimport Interpolator
from pytouhou.formats.animation cimport Animation

cdef class Sprite:
    cdef public int blendfunc, frame
    cdef public float width_override, height_override, angle
    cdef public bint removed, changed, visible, force_rotation
    cdef public bint automatic_orientation, allow_dest_offset, mirrored
    cdef public bint corner_relative_placement
    cdef public Interpolator scale_interpolator, fade_interpolator
    cdef public Interpolator offset_interpolator, rotation_interpolator
    cdef public Interpolator color_interpolator
    cdef public Animation anm

    cdef void *_rendering_data

    cdef float _dest_offset[3]
    cdef float _texcoords[4]
    cdef float _texoffsets[2]
    cdef float _rescale[2]
    cdef float _scale_speed[2]
    cdef float _rotations_3d[3]
    cdef float _rotations_speed_3d[3]
    cdef unsigned char _color[4]

    cpdef fade(self, unsigned int duration, alpha, formula=*)
    cpdef scale_in(self, unsigned int duration, sx, sy, formula=*)
    cpdef move_in(self, unsigned int duration, x, y, z, formula=*)
    cpdef rotate_in(self, unsigned int duration, rx, ry, rz, formula=*)
    cpdef change_color_in(self, unsigned int duration, r, g, b, formula=*)
    cpdef update_orientation(self, double angle_base=*, bint force_rotation=*)
    cpdef Sprite copy(self)
    cpdef update(self)
