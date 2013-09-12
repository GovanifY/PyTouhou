from pytouhou.game.effect cimport Effect
from pytouhou.game.player cimport Player

cdef class Game:
    cdef public long width, height, nb_bullets_max, stage, rank, difficulty, difficulty_counter, difficulty_min, difficulty_max, frame, last_keystate
    cdef public list bullet_types, laser_types, item_types, players, enemies, effects, bullets, lasers, cancelled_bullets, players_bullets, players_lasers, items, labels, faces, texts, hints, bonus_list
    cdef public object interface, boss, msg_runner, prng, sfx_player
    cdef public double continues
    cdef public Effect spellcard_effect
    cdef public tuple spellcard
    cdef public bint time_stop, msg_wait
    cdef public unsigned short deaths_count, next_bonus

    cpdef modify_difficulty(self, long diff)
    cpdef drop_bonus(self, double x, double y, long _type, end_pos=*)
    cdef void autocollect(self, Player player)
    cpdef cancel_bullets(self)
    cpdef new_particle(self, pos, long anim, long amp, long number=*, bint reverse=*, long duration=*)
    cpdef new_label(self, pos, str text)
    cdef void update_background(self)
    cdef void update_enemies(self)
    cdef void update_msg(self, long keystate) except *
    cdef void update_players(self, long keystate) except *
    cdef void update_effects(self)
    cdef void update_hints(self)
    cdef void update_faces(self)
    cdef void update_bullets(self)
    cpdef cleanup(self)
