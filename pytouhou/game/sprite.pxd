from pytouhou.utils.interpolator cimport Interpolator

cdef class Sprite:
    cdef public long width_override, height_override, blendfunc, frame
    cdef public double angle
    cdef public bint removed, changed, visible, force_rotation
    cdef public bint automatic_orientation, allow_dest_offset, mirrored
    cdef public bint corner_relative_placement
    cdef public Interpolator scale_interpolator, fade_interpolator
    cdef public Interpolator offset_interpolator, rotation_interpolator
    cdef public Interpolator color_interpolator
    cdef public tuple texcoords, dest_offset, texoffsets, rescale, scale_speed
    cdef public tuple rotations_3d, rotations_speed_3d, color
    cdef public unsigned char alpha
    cdef public object anm, _rendering_data

    cpdef fade(self, unsigned long duration, alpha, formula=*)
    cpdef scale_in(self, unsigned long duration, sx, sy, formula=*)
    cpdef move_in(self, unsigned long duration, x, y, z, formula=*)
    cpdef rotate_in(self, unsigned long duration, rx, ry, rz, formula=*)
    cpdef change_color_in(self, unsigned long duration, r, g, b, formula=*)
    cpdef update_orientation(self, double angle_base=*, bint force_rotation=*)
    cpdef Sprite copy(self)
    cpdef update(self)
