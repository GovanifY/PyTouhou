# -*- encoding: utf-8 -*-
##
## Copyright (C) 2011 Thibaut Girka <thib@sitedethib.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##


from math import atan2, cos, sin, pi

from pytouhou.utils.helpers import get_logger

from pytouhou.vm.common import MetaRegistry, instruction

logger = get_logger(__name__)



class ECLMainRunner(object):
    __metaclass__ = MetaRegistry
    __slots__ = ('_ecl', '_new_enemy_func', '_game_state', 'processes',
                 'instruction_pointer')

    def __init__(self, ecl, new_enemy_func, game_state):
        self._ecl = ecl
        self._new_enemy_func = new_enemy_func
        self._game_state = game_state

        self.processes = []

        self.instruction_pointer = 0


    def run_iter(self):
        while True:
            try:
                frame, sub, instr_type, args = self._ecl.main[self.instruction_pointer]
            except IndexError:
                break

            if frame > self._game_state.frame:
                break
            else:
                self.instruction_pointer += 1

            if frame == self._game_state.frame:
                try:
                    callback = self._handlers[instr_type]
                except KeyError:
                    logger.warn('unhandled main opcode %d (args: %r)', instr_type, args)
                else:
                    callback(self, sub, instr_type, *args)

        self.processes[:] = (process for process in self.processes
                                                if process.run_iteration())


    @instruction(0)
    @instruction(2)
    @instruction(4)
    @instruction(6)
    def pop_enemy(self, sub, instr_type, x, y, z, life, bonus_dropped, unknown2, unknown3):
        if self._game_state.boss:
            return
        if instr_type & 4:
            if x < -990: #102h.exe@0x411820
                x = self._game_state.prng.rand_double() * 368
            if y < -990: #102h.exe@0x41184b
                y = self._game_state.prng.rand_double() * 416
            if z < -990: #102h.exe@0x411881
                y = self._game_state.prng.rand_double() * 800
        enemy = self._new_enemy_func((x, y), life, instr_type, self.pop_enemy)
        process = ECLRunner(self._ecl, sub, enemy, self._game_state)
        self.processes.append(process)
        process.run_iteration()




class ECLRunner(object):
    __metaclass__ = MetaRegistry
    __slots__ = ('_ecl', '_enemy', '_game_state', 'variables', 'sub', 'frame',
                 'instruction_pointer', 'comparison_reg', 'stack')

    def __init__(self, ecl, sub, enemy, game_state):
        # Things not supposed to change
        self._ecl = ecl
        self._enemy = enemy
        self._game_state = game_state

        # Things supposed to change (and be put in the stack)
        self.variables = [0,  0,  0,  0,
                          0., 0., 0., 0.,
                          0,  0,  0,  0]
        self.comparison_reg = 0
        self.sub = sub
        self.frame = 0
        self.instruction_pointer = 0

        self.stack = []


    def handle_callbacks(self):
        #TODO: implement missing callbacks and clean up!
        enm = self._enemy
        if enm.boss_callback is not None: #XXX: MSG's job!
            self.frame = 0
            self.sub = enm.boss_callback
            self.instruction_pointer = 0
            enm.boss_callback = None
        if enm.life == 0 and enm.death_callback is not None:
            self.frame = 0
            self.sub = enm.death_callback
            self.instruction_pointer = 0
            #TODO: various things, like deleting the character
            enm.death_callback = None #XXX
        elif enm.timeout and enm.frame == enm.timeout:
            enm.frame = 0
            if enm.timeout_callback is not None:
                self.frame = 0
                self.sub = enm.timeout_callback
                self.instruction_pointer = 0
                enm.timeout_callback = None
            else:
                enm.life = 0
        #TODO: other callbacks (low life, etc.)


    def run_iteration(self):
        # First, if enemy is dead, return
        if self._enemy._removed:
            return False

        # Then, check for callbacks
        self.handle_callbacks()

        # Now, process script
        while True:
            try:
                frame, instr_type, rank_mask, param_mask, args = self._ecl.subs[self.sub][self.instruction_pointer]
            except IndexError:
                return False

            if frame > self.frame:
                break
            else:
                self.instruction_pointer += 1


            #TODO: skip bad ranks
            if not rank_mask & (0x100 << self._game_state.rank):
                continue


            if frame == self.frame:
                try:
                    callback = self._handlers[instr_type]
                except KeyError:
                    logger.warn('unhandled opcode %d (args: %r)', instr_type, args)
                else:
                    callback(self, *args)
                    logger.debug('executed opcode %d (args: %r)', instr_type, args)

        self.frame += 1
        return True


    def _getval(self, value):
        if -10012 <= value <= -10001:
            return self.variables[int(-10001-value)]
        elif -10025 <= value <= -10013:
            if value == -10013:
                return self._game_state.rank
            elif value == -10014:
                return self._game_state.difficulty
            elif value == -10015:
                return self._enemy.x
            elif value == -10016:
                return self._enemy.y
            elif value == -10017:
                return self._enemy.z
            elif value == -10018:
                player = self._enemy.select_player()
                return player.x
            elif value == -10019:
                player = self._enemy.select_player()
                return player.y
            elif value == -10021:
                return self._enemy.get_player_angle()
            elif value == -10022:
                return self._enemy.frame
            elif value == -10024:
                return self._enemy.life
            elif value == -10025:
                return self._enemy.select_player().character
            raise NotImplementedError(value) #TODO
        else:
            return value


    def _setval(self, variable_id, value):
        if -10012 <= variable_id <= -10001:
            self.variables[int(-10001-variable_id)] = value
        elif -10025 <= variable_id <= -10013:
            if variable_id == -10015:
                self._enemy.x = value
            elif variable_id == -10016:
                self._enemy.y = value
            elif variable_id == -10017:
                self._enemy.z = value
            elif variable_id == -10022:
                self._enemy.frame = value
            elif variable_id == -10024:
                self._enemy.life = value
            else:
                raise IndexError #TODO: proper exception
        else:
            raise IndexError #TODO: proper exception


    @instruction(0)
    def noop(self):
        pass #TODO: Really?


    @instruction(1)
    def destroy(self, arg):
        #TODO: arg?
        self._enemy._removed = True


    @instruction(2)
    def relative_jump(self, frame, instruction_pointer):
        """Jumps to a relative offset in the same subroutine.

        Warning: the relative offset has been translated to an instruction pointer
        by the ECL parsing code (see pytouhou.formats.ecl).
        """
        self.frame, self.instruction_pointer = frame, instruction_pointer


    @instruction(3)
    def relative_jump_ex(self, frame, instruction_pointer, variable_id):
        """If the given variable is non-zero, decrease it by 1 and jump to a
        relative offset in the same subroutine.

        Warning: the relative offset has been translated to an instruction pointer
        by the ECL parsing code (see pytouhou.formats.ecl).
        """
        counter_value = self._getval(variable_id) - 1
        if counter_value > 0:
            self._setval(variable_id, counter_value)
            self.frame, self.instruction_pointer = frame, instruction_pointer


    @instruction(4)
    @instruction(5)
    def set_variable(self, variable_id, value):
        self._setval(variable_id, self._getval(value))


    @instruction(6)
    def set_random_int(self, variable_id, maxval):
        """Set the specified variable to a random int in the [0, maxval) range.
        """
        self._setval(variable_id, int(self._getval(maxval) * self._game_state.prng.rand_double()))


    @instruction(8)
    def set_random_float(self, variable_id, maxval):
        """Set the specified variable to a random float in [0, maxval) range.
        """
        self._setval(variable_id, self._getval(maxval) * self._game_state.prng.rand_double())


    @instruction(9)
    def set_random_float2(self, variable_id, minval, amp):
        self._setval(variable_id, self._getval(minval) + self._getval(amp) * self._game_state.prng.rand_double())


    @instruction(10)
    def store_x(self, variable_id):
        self._setval(variable_id, self._enemy.x)


    @instruction(14)
    @instruction(21)
    def substract(self, variable_id, a, b):
        #TODO: 14 takes only ints and 21 only floats.
        # The original engine dereferences the variables in the type it waits for, so this isn't exactly the correct implementation, but the data don't contain such case.
        self._setval(variable_id, self._getval(a) - self._getval(b))


    @instruction(13)
    @instruction(20)
    def add(self, variable_id, a, b):
        #TODO: 13 takes only ints and 20 only floats.
        # The original engine dereferences the variables in the type it waits for, so this isn't exactly the correct implementation, but the data don't contain such case.
        self._setval(variable_id, self._getval(a) + self._getval(b))


    @instruction(15)
    def multiply_int(self, variable_id, a, b):
        #TODO: takes only ints.
        self._setval(variable_id, self._getval(a) * self._getval(b))


    @instruction(16)
    def divide_int(self, variable_id, a, b):
        #TODO: takes only ints.
        self._setval(variable_id, self._getval(a) // self._getval(b))


    @instruction(17)
    def modulo(self, variable_id, a, b):
        self._setval(variable_id, self._getval(a) % self._getval(b))


    @instruction(18)
    def increment(self, variable_id):
        self._setval(variable_id, self._getval(variable_id) + 1)


    @instruction(23)
    def divide_float(self, variable_id, a, b):
        #TODO: takes only floats.
        self._setval(variable_id, self._getval(a) / self._getval(b))


    @instruction(25)
    def get_direction(self, variable_id, x1, y1, x2, y2):
        #TODO: takes only floats.
        self._setval(variable_id, math.atan2(self._getval(y2) - self._getval(y1), self._getval(x2) - self._getval(x1)))


    @instruction(27)
    @instruction(28)
    def compare(self, a, b):
        #TODO: 27 takes only ints and 28 only floats.
        a, b = self._getval(a), self._getval(b)
        if a < b:
            self.comparison_reg = -1
        elif a == b:
            self.comparison_reg = 0
        else:
            self.comparison_reg = 1


    @instruction(29)
    def relative_jump_if_lower_than(self, frame, instruction_pointer):
        if self.comparison_reg == -1:
            self.relative_jump(frame, instruction_pointer)


    @instruction(30)
    def relative_jump_if_lower_or_equal(self, frame, instruction_pointer):
        if self.comparison_reg != 1:
            self.relative_jump(frame, instruction_pointer)


    @instruction(31)
    def relative_jump_if_equal(self, frame, instruction_pointer):
        if self.comparison_reg == 0:
            self.relative_jump(frame, instruction_pointer)


    @instruction(32)
    def relative_jump_if_greater_than(self, frame, instruction_pointer):
        if self.comparison_reg == 1:
            self.relative_jump(frame, instruction_pointer)


    @instruction(33)
    def relative_jump_if_greater_or_equal(self, frame, instruction_pointer):
        if self.comparison_reg != -1:
            self.relative_jump(frame, instruction_pointer)


    @instruction(34)
    def relative_jump_if_not_equal(self, frame, instruction_pointer):
        if self.comparison_reg != 0:
            self.relative_jump(frame, instruction_pointer)


    @instruction(35)
    def call(self, sub, param1, param2):
        self.stack.append((self.sub, self.frame, self.instruction_pointer,
                           self.variables, self.comparison_reg))
        self.sub = sub
        self.frame = 0
        self.instruction_pointer = 0
        self.variables = [param1, 0,  0,  0,
                          param2, 0., 0., 0.,
                          0,      0,  0,  0]


    @instruction(36)
    def ret(self):
        self.sub, self.frame, self.instruction_pointer, self.variables, self.comparison_reg = self.stack.pop()


    @instruction(39)
    def call_if_equal(self, sub, param1, param2, a, b):
        if self._getval(a) == self._getval(b):
            self.call(sub, param1, param2)


    @instruction(43)
    def set_pos(self, x, y, z):
        self._enemy.set_pos(self._getval(x), self._getval(y), self._getval(z))


    @instruction(45)
    def set_angle_speed(self, angle, speed):
        self._enemy.angle, self._enemy.speed = angle, speed


    @instruction(46)
    def set_rotation_speed(self, speed):
        self._enemy.rotation_speed = speed


    @instruction(47)
    def set_speed(self, speed):
        self._enemy.speed = speed


    @instruction(48)
    def set_acceleration(self, acceleration):
        self._enemy.acceleration = acceleration


    @instruction(49)
    def set_random_angle(self, min_angle, max_angle):
        angle = self._game_state.prng.rand_double() * (max_angle - min_angle) + min_angle
        self._enemy.angle = angle


    @instruction(50)
    def set_random_angle_ex(self, min_angle, max_angle):
        if self._enemy.screen_box:
            minx, miny, maxx, maxy = self._enemy.screen_box
        else:
            minx, miny, maxx, maxy = (0., 0., 0., 0.)

        angle = self._game_state.prng.rand_double() * (max_angle - min_angle) + min_angle
        sa, ca = sin(angle), cos(angle)

        distx = min(96.0, (maxx - minx) / 2.)
        disty = min(96.0, (maxy - miny) / 2.)

        if self._enemy.x > maxx - 96.0:
            ca = -abs(ca)
        elif self._enemy.x < minx + 96.0:
            ca = abs(ca)

        if self._enemy.y > maxy - 48.0:
            sa = -abs(sa)
        elif self._enemy.y < miny + 48.0:
            sa = abs(sa)
        self._enemy.angle = atan2(sa, ca)


    @instruction(51)
    def target_player(self, unknown, speed):
        #TODO: unknown
        self._enemy.speed = speed
        self._enemy.angle = self._enemy.get_player_angle()


    @instruction(56)
    def move_to_linear(self, duration, x, y, z):
        self._enemy.move_to(duration, x, y, z, lambda x: x)


    @instruction(57)
    def move_to_decel(self, duration, x, y, z):
        self._enemy.move_to(duration, x, y, z, lambda x: 2. * x - x ** 2)


    @instruction(59)
    def move_to_accel(self, duration, x, y, z):
        self._enemy.move_to(duration, x, y, z, lambda x: x ** 2)


    @instruction(61)
    def stop_in(self, duration):
        self._enemy.stop_in(duration, lambda x: x)


    @instruction(63)
    def stop_in_accel(self, duration):
        self._enemy.stop_in(duration, lambda x: 1. - x)


    @instruction(65)
    def set_screen_box(self, xmin, ymin, xmax, ymax):
        self._enemy.screen_box = xmin, ymin, xmax, ymax


    @instruction(66)
    def clear_screen_box(self):
        self._enemy.screen_box = None


    @instruction(67)
    def set_bullet_attributes1(self, anim, sprite_idx_offset, bullets_per_shot,
                               number_of_shots, speed, speed2, launch_angle,
                               angle, flags):
        self._enemy.set_bullet_attributes(67, anim,
                                          self._getval(sprite_idx_offset),
                                          self._getval(bullets_per_shot),
                                          self._getval(number_of_shots),
                                          self._getval(speed),
                                          self._getval(speed2),
                                          self._getval(launch_angle),
                                          self._getval(angle),
                                          flags)


    @instruction(68)
    def set_bullet_attributes2(self, anim, sprite_idx_offset, bullets_per_shot,
                               number_of_shots, speed, speed2, launch_angle,
                               angle, flags):
        self._enemy.set_bullet_attributes(68, anim,
                                          self._getval(sprite_idx_offset),
                                          self._getval(bullets_per_shot),
                                          self._getval(number_of_shots),
                                          self._getval(speed),
                                          self._getval(speed2),
                                          self._getval(launch_angle),
                                          self._getval(angle),
                                          flags)


    @instruction(69)
    def set_bullet_attributes3(self, anim, sprite_idx_offset, bullets_per_shot,
                               number_of_shots, speed, speed2, launch_angle,
                               angle, flags):
        self._enemy.set_bullet_attributes(69, anim,
                                          self._getval(sprite_idx_offset),
                                          self._getval(bullets_per_shot),
                                          self._getval(number_of_shots),
                                          self._getval(speed),
                                          self._getval(speed2),
                                          self._getval(launch_angle),
                                          self._getval(angle),
                                          flags)


    @instruction(70)
    def set_bullet_attributes4(self, anim, sprite_idx_offset, bullets_per_shot,
                               number_of_shots, speed, speed2, launch_angle,
                               angle, flags):
        self._enemy.set_bullet_attributes(70, anim,
                                          self._getval(sprite_idx_offset),
                                          self._getval(bullets_per_shot),
                                          self._getval(number_of_shots),
                                          self._getval(speed),
                                          self._getval(speed2),
                                          self._getval(launch_angle),
                                          self._getval(angle),
                                          flags)


    @instruction(71)
    def set_bullet_attributes5(self, anim, sprite_idx_offset, bullets_per_shot,
                               number_of_shots, speed, speed2, launch_angle,
                               angle, flags):
        self._enemy.set_bullet_attributes(71, anim,
                                          self._getval(sprite_idx_offset),
                                          self._getval(bullets_per_shot),
                                          self._getval(number_of_shots),
                                          self._getval(speed),
                                          self._getval(speed2),
                                          self._getval(launch_angle),
                                          self._getval(angle),
                                          flags)


    @instruction(74)
    def set_bullet_attributes6(self, anim, sprite_idx_offset, bullets_per_shot,
                               number_of_shots, speed, speed2, launch_angle,
                               angle, flags):
        #TODO
        self._enemy.set_bullet_attributes(74, anim,
                                          self._getval(sprite_idx_offset),
                                          self._getval(bullets_per_shot),
                                          self._getval(number_of_shots),
                                          self._getval(speed),
                                          self._getval(speed2),
                                          self._getval(launch_angle),
                                          self._getval(angle),
                                          flags)


    @instruction(75)
    def set_bullet_attributes7(self, anim, sprite_idx_offset, bullets_per_shot,
                               number_of_shots, speed, speed2, launch_angle,
                               angle, flags):
        #TODO
        self._enemy.set_bullet_attributes(75, anim,
                                          self._getval(sprite_idx_offset),
                                          self._getval(bullets_per_shot),
                                          self._getval(number_of_shots),
                                          self._getval(speed),
                                          self._getval(speed2),
                                          self._getval(launch_angle),
                                          self._getval(angle),
                                          flags)


    @instruction(76)
    def set_bullet_interval(self, value):
        self._enemy.bullet_launch_interval = value


    @instruction(77)
    def set_bullet_interval_ex(self, value):
        self._enemy.bullet_launch_interval = value
        self._enemy.bullet_launch_timer = int(self._game_state.prng.rand_double() * value) #TODO: check


    @instruction(78)
    def set_delay_attack(self):
        self._enemy.delay_attack = True


    @instruction(79)
    def set_no_delay_attack(self):
        self._enemy.delay_attack = False


    @instruction(81)
    def set_bullet_launch_offset(self, x, y, z):
        self._enemy.bullet_launch_offset = (self._getval(x), self._getval(y))


    @instruction(82)
    def set_extended_bullet_attributes(self, *attributes):
        self._enemy.extended_bullet_attributes = tuple(self._getval(attr) for attr in attributes)


    @instruction(93)
    def set_spellcard(self, unknown, number, name):
        #TODO: display it on the game.
        print("%d - %s" % (number, name))


    @instruction(95)
    def pop_enemy(self, sub, x, y, z, life, bonus_dropped, unknown2):
        self._enemy.pop_enemy(sub, 0, self._getval(x), self._getval(y), 0, life, bonus_dropped, unknown2, 0) # TODO: check about unknown values


    @instruction(97)
    def set_anim(self, sprite_index):
        self._enemy.set_anim(sprite_index)


    @instruction(98)
    def set_multiple_anims(self, default, end_left, end_right, left, right):
        self._enemy.movement_dependant_sprites = end_left, end_right, left, right
        self._enemy.set_anim(default)


    @instruction(100)
    def set_death_anim(self, sprite_index):
        self._enemy.death_anim = sprite_index % 256 #TODO


    @instruction(101)
    def set_boss_mode(self, unknown):
        #TODO: unknown
        self._game_state.boss = self._enemy


    @instruction(103)
    def set_hitbox(self, width, height, depth):
        self._enemy.hitbox = (width, height)


    @instruction(104)
    def set_collidable(self, collidable):
        """Defines whether the enemy is “collidable”.
        A collision between a collidable enemy and the player will kill the player.
        """
        self._enemy.collidable = bool(collidable & 1)


    @instruction(105)
    def set_damageable(self, damageable):
        self._enemy.damageable = bool(damageable & 1)


    @instruction(107)
    def set_death_flags(self, death_flags):
        self._enemy.death_flags = death_flags


    @instruction(108)
    def set_death_callback(self, sub):
        self._enemy.death_callback = sub


    @instruction(109)
    def memory_write(self, value, index):
        #TODO
        #XXX: this is a hack to display bosses although we don't handle MSG :)
        if index == 0:
            self._enemy.boss_callback = value
        else:
            raise Exception #TODO


    @instruction(111)
    def set_life(self, value):
        self._enemy.life = value


    @instruction(112)
    def set_ellapsed_time(self, value):
        """Sets the enemy's frame counter.
        This is used for timeouts, where the framecounter is compared to the
        timeout value (what's displayed is (enemy.timeout - enemy.frame) // 60).
        """
        self._enemy.frame = value


    @instruction(113)
    def set_low_life_trigger(self, value):
        self._enemy.low_life_trigger = value


    @instruction(114)
    def set_low_life_callback(self, sub):
        self._enemy.low_life_callback = sub


    @instruction(115)
    def set_timeout(self, timeout):
        self._enemy.timeout = timeout


    @instruction(116)
    def set_timeout_callback(self, sub):
        self._enemy.timeout_callback = sub


    @instruction(117)
    def set_touchable(self, value):
        """Defines whether the enemy is “touchable”.
        Bullets only collide with an enemy if it is “touchable”.
        Likewise, ReimuA's homing attacks only target “touchable” enemies.
        """
        self._enemy.touchable = bool(value)


    @instruction(120)
    def set_automatic_orientation(self, flags):
        #TODO: does it change anything else than the sprite's rotation?
        self._enemy.automatic_orientation = bool(flags & 1)


    @instruction(121)
    def call_special_function(self, function, arg):
        if function == 0: # Cirno
            if arg == 0:
                for bullet in self._game_state.bullets:
                    bullet.speed = bullet.angle = 0.
                    bullet.delta = (0., 0.)
                    bullet.set_anim(sprite_idx_offset=15) #TODO: check
            else:
                for bullet in self._game_state.bullets:
                    bullet.speed = 2.0 #TODO
                    bullet.angle = self._game_state.prng.rand_double() * pi #TODO
                    bullet.delta = (cos(bullet.angle) * bullet.speed, sin(bullet.angle) * bullet.speed)
        else:
            logger.warn("Unimplemented special function %d!", function)


    @instruction(123)
    def skip_frames(self, frames):
        #TODO: is that all?
        self.frame += self._getval(frames)


    @instruction(126)
    def set_remaining_lives(self, lives):
        self._enemy.remaining_lives = lives

