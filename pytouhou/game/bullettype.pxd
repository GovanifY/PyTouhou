cdef class BulletType:
    cdef public long type_id
    cdef long anim_index, hitbox_size, cancel_anim_index
    cdef long launch_anim2_index, launch_anim4_index, launch_anim8_index
    cdef tuple launch_anim_offsets
    cdef float launch_anim_penalties[3]
    cdef object anm
