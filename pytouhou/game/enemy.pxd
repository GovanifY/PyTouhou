from pytouhou.game.element cimport Element
from pytouhou.game.game cimport Game
from pytouhou.game.player cimport Player
from pytouhou.utils.interpolator cimport Interpolator

cdef class Callback:
    cdef function
    cdef public tuple args  # XXX: public only for ECL’s copy_callbacks.

    cpdef enable(self, function, tuple args)
    cpdef disable(self)
    cpdef fire(self)

cdef class Enemy(Element):
    cdef public double z, angle, speed, rotation_speed, acceleration
    cdef public long _type, bonus_dropped, die_score, frame, life, death_flags, current_laser_id, low_life_trigger, timeout, remaining_lives, bullet_launch_interval, bullet_launch_timer, death_anim, direction, update_mode
    cdef public bint visible, was_visible, touchable, collidable, damageable, boss, automatic_orientation, delay_attack
    cdef public tuple difficulty_coeffs, extended_bullet_attributes, bullet_attributes, bullet_launch_offset, movement_dependant_sprites, screen_box
    cdef public Callback death_callback, boss_callback, low_life_callback, timeout_callback
    cdef public dict laser_by_id
    cdef public list aux_anm
    cdef public Interpolator interpolator, speed_interpolator
    cdef public object _anms, process

    cdef Game _game
    cdef double[2] hitbox_half_size

    cpdef play_sound(self, index)
    cpdef set_hitbox(self, double width, double height)
    cpdef set_bullet_attributes(self, type_, anim, sprite_idx_offset,
                                unsigned long bullets_per_shot,
                                unsigned long number_of_shots, double speed,
                                double speed2, launch_angle, angle, flags)
    cpdef set_bullet_launch_interval(self, long value, unsigned long start=*)
    cpdef fire(self, offset=*, bullet_attributes=*, tuple launch_pos=*)
    cpdef new_laser(self, unsigned long variant, laser_type, sprite_idx_offset,
                    double angle, speed, start_offset, end_offset, max_length,
                    width, start_duration, duration, end_duration,
                    grazing_delay, grazing_extra_duration, unknown,
                    tuple offset=*)
    cpdef Player select_player(self, list players=*)
    cpdef double get_angle(self, Element target, tuple pos=*) except 42
    cpdef set_anim(self, index)
    cdef bint die_anim(self) except True
    cdef bint drop_particles(self, long number, long color) except True
    cpdef set_aux_anm(self, long number, long index)
    cpdef set_pos(self, double x, double y, double z)
    cpdef move_to(self, unsigned long duration, double x, double y, double z, formula)
    cpdef stop_in(self, unsigned long duration, formula)
    cpdef set_boss(self, bint enable)
    cdef bint is_visible(self, long screen_width, long screen_height) except -1
    cdef bint check_collisions(self) except True
    cdef bint handle_callbacks(self) except True
    cdef bint update(self) except True
