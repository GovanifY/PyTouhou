from pytouhou.game.effect cimport Effect
from pytouhou.game.player cimport Player
from pytouhou.game.text cimport Text, NativeText
from pytouhou.game.music cimport MusicPlayer
from pytouhou.utils.random cimport Random

cdef class Game:
    cdef public long width, height, nb_bullets_max, stage, rank, difficulty, difficulty_min, difficulty_max, frame
    cdef public list bullet_types, laser_types, item_types, players, enemies, effects, bullets, lasers, cancelled_bullets, players_bullets, players_lasers, items, labels, faces, hints, bonus_list
    cdef public object interface, boss, msg_runner
    cdef public dict texts
    cdef public MusicPlayer sfx_player
    cdef public Random prng
    cdef public double continues
    cdef public Effect spellcard_effect
    cdef public tuple spellcard
    cdef public bint time_stop, msg_wait
    cdef public unsigned short deaths_count, next_bonus

    cdef long difficulty_counter, last_keystate
    cdef bint friendly_fire

    cdef list msg_sprites(self)
    cdef list lasers_sprites(self)
    cdef void modify_difficulty(self, long diff) nogil
    cpdef enable_spellcard_effect(self)
    cpdef disable_spellcard_effect(self)
    cdef void set_player_bomb(self) except *
    cdef void unset_player_bomb(self) except *
    cpdef drop_bonus(self, double x, double y, long _type, end_pos=*, player=*)
    cdef void autocollect(self, Player player) except *
    cdef void cancel_bullets(self) except *
    cdef void cancel_player_lasers(self) except *
    cpdef change_bullets_into_star_items(self)
    cpdef change_bullets_into_bonus(self)
    cpdef kill_enemies(self)
    cpdef new_effect(self, pos, long anim, anm=*, long number=*)
    cpdef new_particle(self, pos, long anim, long amp, long number=*, bint reverse=*, long duration=*)
    cpdef new_enemy(self, pos, life, instr_type, bonus_dropped, die_score)
    cpdef new_msg(self, sub)
    cdef Text new_label(self, tuple pos, bytes text)
    cpdef NativeText new_native_text(self, tuple pos, unicode text, align=*)
    cpdef Text new_hint(self, hint)
    cpdef new_face(self, side, effect)
    cpdef run_iter(self, list keystates)
    cdef void update_background(self) except *
    cdef void update_enemies(self) except *
    cdef void update_msg(self, long keystate) except *
    cdef void update_players(self, list keystates) except *
    cdef void update_effects(self) except *
    cdef void update_hints(self) except *
    cdef void update_faces(self) except *
    cdef void update_bullets(self) except *
    cpdef cleanup(self)
