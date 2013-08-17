from pytouhou.game.element cimport Element
from pytouhou.game.game cimport Game
from pytouhou.utils.interpolator cimport Interpolator

cdef class Enemy(Element):
    cdef public double z, angle, speed, rotation_speed, acceleration
    cdef public long _type, bonus_dropped, die_score, frame, life, death_flags, current_laser_id, death_callback, boss_callback, low_life_callback, low_life_trigger, timeout, timeout_callback, remaining_lives, bullet_launch_interval, bullet_launch_timer, death_anim, direction, update_mode
    cdef public bint visible, was_visible, touchable, collidable, damageable, boss, automatic_orientation, delay_attack
    cdef public tuple difficulty_coeffs, extended_bullet_attributes, bullet_attributes, bullet_launch_offset, movement_dependant_sprites, screen_box
    cdef public dict laser_by_id
    cdef public list aux_anm
    cdef public Interpolator interpolator, speed_interpolator
    cdef public object _anms, process

    cdef Game _game
    cdef double[2] hitbox_half_size

    cpdef play_sound(self, index)
    cpdef set_hitbox(self, double width, double height)
    cpdef set_bullet_attributes(self, type_, anim, sprite_idx_offset,
                                bullets_per_shot, number_of_shots, speed, speed2,
                                launch_angle, angle, flags)
    cpdef set_bullet_launch_interval(self, long value, unsigned long start=*)
    cpdef fire(self, offset=*, bullet_attributes=*, launch_pos=*)
    cpdef new_laser(self, variant, laser_type, sprite_idx_offset, angle, speed,
                    start_offset, end_offset, max_length, width,
                    start_duration, duration, end_duration,
                    grazing_delay, grazing_extra_duration, unknown,
                    offset=*)
    cpdef select_player(self, players=*)
    cpdef get_player_angle(self, player=*, pos=*)
    cpdef set_anim(self, index)
    cdef void die_anim(self)
    cdef void drop_particles(self, long number, long color)
    cpdef set_aux_anm(self, long number, long index)
    cpdef set_pos(self, x, y, z)
    cpdef move_to(self, duration, x, y, z, formula)
    cpdef stop_in(self, duration, formula)
    cdef bint is_visible(self, long screen_width, long screen_height)
    cdef void check_collisions(self)
    cdef void handle_callbacks(self)
    cpdef update(self)
