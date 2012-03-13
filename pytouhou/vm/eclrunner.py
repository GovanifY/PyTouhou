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
    __slots__ = ('_ecl', '_game', 'processes', 'frame',
                 'instruction_pointer',
                 'boss_wait')

    def __init__(self, ecl, game):
        self._ecl = ecl
        self._game = game
        self.frame = 0
        self.boss_wait = False

        self.processes = []

        self.instruction_pointer = 0


    def run_iter(self):
        if not self._game.boss:
            self.boss_wait = False

        while True:
            try:
                frame, sub, instr_type, args = self._ecl.main[self.instruction_pointer]
            except IndexError:
                break

            # The msg_wait instruction stops the reading of the ECL, not just the frame incrementation.
            if frame > self.frame or self._game.msg_wait or self.boss_wait:
                break
            else:
                self.instruction_pointer += 1

            if frame == self.frame:
                try:
                    callback = self._handlers[instr_type]
                except KeyError:
                    logger.warn('unhandled main opcode %d (args: %r)', instr_type, args)
                else:
                    callback(self, sub, instr_type, *args)

        self.processes[:] = (process for process in self.processes
                                                if process.run_iteration())

        if not (self._game.msg_wait or self.boss_wait):
            self.frame += 1


    def _pop_enemy(self, sub, instr_type, x, y, z, life, bonus_dropped, die_score):
        if instr_type & 4:
            if x < -990: #102h.exe@0x411820
                x = self._game.prng.rand_double() * 368
            if y < -990: #102h.exe@0x41184b
                y = self._game.prng.rand_double() * 416
            if z < -990: #102h.exe@0x411881
                z = self._game.prng.rand_double() * 800
        enemy = self._game.new_enemy((x, y, z), life, instr_type, bonus_dropped, die_score)
        process = ECLRunner(self._ecl, sub, enemy, self._game)
        self.processes.append(process)
        process.run_iteration()


    @instruction(0)
    @instruction(2)
    @instruction(4)
    @instruction(6)
    def pop_enemy(self, sub, instr_type, x, y, z, life, bonus_dropped, die_score):
        if self._game.boss:
            return
        self._pop_enemy(sub, instr_type, x, y, z, life, bonus_dropped, die_score)


    @instruction(8)
    def call_msg(self, sub, instr_type):
        self._game.new_msg(sub)


    @instruction(9)
    def wait_msg(self, sub, instr_type):
        self._game.msg_wait = True


    @instruction(10)
    def resume_ecl(self, sub, instr_type, unk1, unk2):
        boss = self._game.boss
        self._game.msg_wait = False
        if boss._enemy.boss_callback > -1:
            boss.switch_to_sub(boss._enemy.boss_callback)
            boss._enemy.boss_callback = -1
        else:
            raise Exception #TODO


    @instruction(12)
    def wait_for_boss_death(self, sub, instr_type):
        self.boss_wait = True




class ECLRunner(object):
    __metaclass__ = MetaRegistry
    __slots__ = ('_ecl', '_enemy', '_game', 'variables', 'sub', 'frame',
                 'instruction_pointer', 'comparison_reg', 'stack')

    def __init__(self, ecl, sub, enemy, game):
        # Things not supposed to change
        self._ecl = ecl
        self._enemy = enemy
        self._game = game

        # Things supposed to change (and be put in the stack)
        self.variables = [0,  0,  0,  0,
                          0., 0., 0., 0.,
                          0,  0,  0,  0]
        self.comparison_reg = 0
        self.switch_to_sub(sub)

        self.stack = []


    def switch_to_sub(self, sub):
        self.frame = 0
        self.sub = sub
        self.instruction_pointer = 0


    def handle_callbacks(self):
        #TODO: implement missing callbacks and clean up!
        enm = self._enemy
        if enm.life <= 0 and enm.touchable:
            death_flags = enm.death_flags & 7

            enm.die_anim()

            if death_flags < 4:
                if enm.bonus_dropped > -1:
                    enm.drop_particles(7, 0)
                    self._game.drop_bonus(enm.x, enm.y, enm.bonus_dropped)
                elif enm.bonus_dropped == -1:
                    if self._game.deaths_count % 3 == 0:
                        enm.drop_particles(10, 0)
                        self._game.drop_bonus(enm.x, enm.y, self._game.bonus_list[self._game.next_bonus])
                        self._game.next_bonus = (self._game.next_bonus + 1) % 32
                    else:
                        enm.drop_particles(4, 0)
                    self._game.deaths_count += 1
                else:
                    enm.drop_particles(4, 0)

                if death_flags == 0:
                    enm.removed = True
                    return

                if death_flags == 1:
                    enm.touchable = False
                elif death_flags == 2:
                    pass # Just that?
                elif death_flags == 3:
                    #TODO: disable boss mode
                    enm.damageable = False
                    enm.life = 1
                    enm.death_flags = 0

            if death_flags != 0 and enm.death_callback > -1:
                self.switch_to_sub(enm.death_callback)
                enm.death_callback = -1
        elif enm.life <= enm.low_life_trigger and enm.low_life_callback > -1:
            self.switch_to_sub(enm.low_life_callback)
            enm.low_life_callback = -1
        elif enm.timeout != -1 and enm.frame == enm.timeout:
            enm.frame = 0
            if enm.timeout_callback > -1:
                self.switch_to_sub(enm.timeout_callback)
                enm.timeout_callback = -1
            elif enm.touchable:
                enm.life = 0
            elif enm.death_callback > -1:
                self.switch_to_sub(enm.death_callback)
                enm.death_callback = -1
                enm.timeout = -1 #TODO: check
            else:
                raise Exception('What the hell, man!')

    def run_iteration(self):
        # First, if enemy is dead, return
        if self._enemy.removed:
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

            if not rank_mask & (0x100 << self._game.rank):
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
                return self._game.rank
            elif value == -10014:
                return self._game.difficulty
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
                return self._enemy.select_player().state.character #TODO
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
        self._enemy.removed = True


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
        self._setval(variable_id, int(self._getval(maxval) * self._game.prng.rand_double()))


    @instruction(8)
    def set_random_float(self, variable_id, maxval):
        """Set the specified variable to a random float in [0, maxval) range.
        """
        self._setval(variable_id, self._getval(maxval) * self._game.prng.rand_double())


    @instruction(9)
    def set_random_float2(self, variable_id, amp, minval):
        self._setval(variable_id, self._getval(minval) + self._getval(amp) * self._game.prng.rand_double())


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
        self._setval(variable_id, atan2(self._getval(y2) - self._getval(y1), self._getval(x2) - self._getval(x1)))


    @instruction(26)
    def float_to_unit_circle(self, variable_id):
        #TODO: takes only floats.
        self._setval(variable_id, (self._getval(variable_id) + pi) % (2*pi) - pi)


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
                           list(self.variables), self.comparison_reg))
        self.variables[0] = param1
        self.variables[4] = param2
        self.switch_to_sub(sub)


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
        self._enemy.update_mode = 0
        self._enemy.angle, self._enemy.speed = self._getval(angle), self._getval(speed)


    @instruction(46)
    def set_rotation_speed(self, speed):
        self._enemy.update_mode = 0
        self._enemy.rotation_speed = self._getval(speed)


    @instruction(47)
    def set_speed(self, speed):
        self._enemy.update_mode = 0
        self._enemy.speed = self._getval(speed)


    @instruction(48)
    def set_acceleration(self, acceleration):
        self._enemy.update_mode = 0
        self._enemy.acceleration = self._getval(acceleration)


    @instruction(49)
    def set_random_angle(self, min_angle, max_angle):
        angle = self._game.prng.rand_double() * (max_angle - min_angle) + min_angle
        self._enemy.angle = angle


    @instruction(50)
    def set_random_angle_ex(self, min_angle, max_angle):
        if self._enemy.screen_box:
            minx, miny, maxx, maxy = self._enemy.screen_box
        else:
            minx, miny, maxx, maxy = (0., 0., 0., 0.)

        angle = self._game.prng.rand_double() * (max_angle - min_angle) + min_angle
        sa, ca = sin(angle), cos(angle)

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
        self._enemy.update_mode = 0
        self._enemy.speed = speed
        self._enemy.angle = self._enemy.get_player_angle()


    @instruction(52)
    def move_in_decel(self, duration, angle, speed):
        self._enemy.angle, self._enemy.speed = angle, speed
        self._enemy.stop_in(duration, lambda x: 2. * x - x ** 2)


    @instruction(56)
    def move_to_linear(self, duration, x, y, z):
        self._enemy.move_to(duration,
                            self._getval(x), self._getval(y), self._getval(z),
                            lambda x: x)


    @instruction(57)
    def move_to_decel(self, duration, x, y, z):
        self._enemy.move_to(duration,
                            self._getval(x), self._getval(y), self._getval(z),
                            lambda x: 2. * x - x ** 2)


    @instruction(59)
    def move_to_accel(self, duration, x, y, z):
        self._enemy.move_to(duration,
                            self._getval(x), self._getval(y), self._getval(z),
                            lambda x: x ** 2)


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
        self._enemy.set_bullet_launch_interval(value)


    @instruction(77)
    def set_bullet_interval_ex(self, value):
        self._enemy.set_bullet_launch_interval(value, self._game.prng.rand_double()) #TODO: check


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


    @instruction(83)
    def change_bullets_into_star_items(self):
        self._game.change_bullets_into_star_items()


    @instruction(85)
    def new_laser(self, laser_type, sprite_idx_offset, angle, speed,
                  start_offset, end_offset, max_length, width,
                  start_duration, duration, end_duration,
                  grazing_delay, grazing_extra_duration, unknown):
        self._enemy.new_laser(85, laser_type, sprite_idx_offset, self._getval(angle), speed,
                              start_offset, end_offset, max_length, width,
                              start_duration, duration, end_duration,
                              grazing_delay, grazing_extra_duration, unknown)


    @instruction(86)
    def new_laser_towards_player(self, laser_type, sprite_idx_offset, angle, speed,
                                 start_offset, end_offset, max_length, width,
                                 start_duration, duration, end_duration,
                                 grazing_delay, grazing_extra_duration, unknown):
        self._enemy.new_laser(86, laser_type, sprite_idx_offset, self._getval(angle), speed,
                              start_offset, end_offset, max_length, width,
                              start_duration, duration, end_duration,
                              grazing_delay, grazing_extra_duration, unknown)


    @instruction(87)
    def set_upcoming_laser_id(self, laser_id):
        self._enemy.current_laser_id = laser_id


    @instruction(88)
    def alter_laser_angle(self, laser_id, delta):
        try:
            laser = self._enemy.laser_by_id[laser_id]
        except KeyError:
            pass #TODO
        else:
            laser.angle += self._getval(delta)


    @instruction(90)
    def reposition_laser(self, laser_id, ox, oy, oz):
        try:
            laser = self._enemy.laser_by_id[laser_id]
        except KeyError:
            pass #TODO
        else:
            laser.base_pos = self._enemy.x + ox, self._enemy.y + oy


    @instruction(92)
    def cancel_laser(self, laser_id):
        try:
            laser = self._enemy.laser_by_id[laser_id]
        except KeyError:
            pass #TODO
        else:
            laser.cancel()


    @instruction(93)
    def set_spellcard(self, face, number, name):
        #TODO: display it on the game.
        self._enemy.difficulty_coeffs = (-.5, .5, 0, 0, 0, 0)
        self._game.change_bullets_into_star_items()
        self._game.spellcard = (number, name)
        self._game.enable_spellcard_effect()


    @instruction(94)
    def end_spellcard(self):
        #TODO: return everything back to normal
        #TODO: give the spellcard bonus.
        if self._game.spellcard:
            self._game.change_bullets_into_star_items()
        self._game.spellcard = None
        self._game.disable_spellcard_effect()


    @instruction(95)
    def pop_enemy(self, sub, x, y, z, life, bonus_dropped, die_score):
        self._game.ecl_runner._pop_enemy(sub, 0, self._getval(x),
                                                 self._getval(y),
                                                 self._getval(z),
                                                 life, bonus_dropped, die_score)


    @instruction(96)
    def kill_enemies(self):
        for proc in self._game.ecl_runner.processes:
            if proc._enemy.boss:
                pass # Bosses are immune to 96
            elif proc._enemy.touchable:
                proc._enemy.life = 0
            elif proc._enemy.death_callback > 0:
                #TODO: check
                #TODO: refactor
                self.switch_to_sub(proc._enemy.death_callback)
                proc._enemy.death_callback = -1


    @instruction(97)
    def set_anim(self, script):
        self._enemy.set_anim(script)


    @instruction(98)
    def set_multiple_anims(self, default, end_left, end_right, left, right):
        if left == -1:
            self._enemy.movement_dependant_sprites = None
        else:
            self._enemy.movement_dependant_sprites = end_left, end_right, left, right
            self._enemy.set_anim(default)


    @instruction(99)
    def set_aux_anm(self, number, script):
        self._enemy.set_aux_anm(number, script)


    @instruction(100)
    def set_death_anim(self, sprite_index):
        self._enemy.death_anim = sprite_index


    @instruction(101)
    def set_boss_mode(self, value):
        #TODO: if there are multiple boss, spawned by a 95,
        #      only the last one has her life displayed,
        #      but standard enemies are blocked only until any of them is killed.
        if value == 0:
            self._enemy.boss = True
            self._game.boss = self
        elif value == -1:
            self._enemy.boss = False
            self._game.boss = None
        else:
            raise Exception #TODO


    @instruction(103)
    def set_hitbox(self, width, height, depth):
        self._enemy.hitbox = (width, height)
        self._enemy.hitbox_half_size = (width / 2., height / 2.)


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
        #TODO: the enemy's life bar fills in 100 frames.
        # During those frames, the ECL doesn't seem to be executed.
        # However, the ECL isn't directly paused by this instruction itself.
        self._enemy.low_life_trigger = value


    @instruction(114)
    def set_low_life_callback(self, sub):
        self._enemy.low_life_callback = sub


    @instruction(115)
    def set_timeout(self, timeout):
        self._enemy.frame = 0
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


    @instruction(119)
    def drop_some_bonus(self, number):
        if self._enemy.select_player().state.power < 128:
            if number > 0:
                #TODO: find the real formula in the binary.
                self._game.drop_bonus(self._enemy.x - 64 + self._game.prng.rand_double() * 128,
                                      self._enemy.y - 64 + self._game.prng.rand_double() * 128,
                                      2)
            for i in xrange(number - 1):
                self._game.drop_bonus(self._enemy.x - 64 + self._game.prng.rand_double() * 128,
                                      self._enemy.y - 64 + self._game.prng.rand_double() * 128,
                                      0)
        else:
            for i in xrange(number):
                self._game.drop_bonus(self._enemy.x - 64 + self._game.prng.rand_double() * 128,
                                      self._enemy.y - 64 + self._game.prng.rand_double() * 128,
                                      1)


    @instruction(120)
    def set_automatic_orientation(self, flags):
        #TODO: does it change anything else than the sprite's rotation?
        self._enemy.automatic_orientation = bool(flags & 1)


    @instruction(121)
    def call_special_function(self, function, arg):
        if function == 0: # Cirno
            if arg == 0:
                self._game.new_effect((self._enemy.x, self._enemy.y), 17)
                for bullet in self._game.bullets:
                    bullet.speed = bullet.angle = 0.
                    bullet.dx, bullet.dy = 0., 0.
                    bullet.set_anim(sprite_idx_offset=15) #TODO: check
            else:
                self._game.new_effect((self._enemy.x, self._enemy.y), 17)
                for bullet in self._game.bullets:
                    bullet.flags = 16 #TODO: check
                    angle = pi + self._game.prng.rand_double() * 2. * pi
                    bullet.attributes[4:6] = [0.01, angle] #TODO: check
                    bullet.attributes[0] = -1 #TODO: check
                    bullet.set_anim(sprite_idx_offset=15) #TODO: check
        elif function == 1: # Cirno
            offset = (self._game.prng.rand_uint16() % arg - arg / 2,
                      self._game.prng.rand_uint16() % arg - arg / 2)
            self._enemy.fire(offset=offset)
        elif function == 3: # Patchouli’s dual sign spellcards
            values = [[0, 3, 1],
                      [2, 3, 4],
                      [1, 4, 0],
                      [4, 2, 3]]
            character = self._enemy.select_player().state.character
            self.variables[1:4] = values[character]
        elif function == 4:
            if arg == 1:
                self._game.time_stop = True
            else:
                self._game.time_stop = False
        elif function == 8: # Remilia’s magic
            bullet_attributes = [70, 1, 1, 1, 1, 0., 0., 0., 0.7, 0]
            n = 0
            for bullet in self._game.bullets:
                if bullet._bullet_type.anim_index < 5:
                    continue
                n += 1
                bullet_attributes[8] = bullet.angle
                self._enemy.fire(launch_pos=(bullet.x, bullet.y),
                                 bullet_attributes=bullet_attributes)
            self._setval(-10004, n)
        elif function == 13:
            if self._enemy.bullet_attributes is None:
                return

            frame = self._getval(-10004)
            self._setval(-10004, frame + 1)

            if frame % 6 != 0:
                return

            (type_, anim, sprite_idx_offset, bullets_per_shot, number_of_shots,
             speed, speed2, launch_angle, angle, flags) = self._enemy.bullet_attributes
            for i in range(arg):
                _angle = i*2*pi/arg + self._getval(-10007)
                _distance = self._getval(-10008)
                launch_pos = (192 + cos(_angle) * _distance,
                              224 + sin(_angle) * _distance)
                bullet_attributes = (type_, anim, sprite_idx_offset,
                                     bullets_per_shot, number_of_shots,
                                     speed, speed2,
                                     self._getval(-10006) + _angle, angle, flags)
                self._enemy.fire(launch_pos=launch_pos,
                                 bullet_attributes=bullet_attributes)
        elif function == 14: # Laevateinn
            if arg == 0:
                self.variables[4] = 0
                for laser in self._enemy.laser_by_id.values():
                    self.variables[4] += 1
                    for pos in laser.get_bullets_pos():
                        self._enemy.fire(launch_pos=pos)
            else:
                pass #TODO: check
        elif function == 16: # QED: Ripples of 495 years
            #TODO: the rythm seems to be really wrong
            # Indeed, Flandre is supposed to start slowly, and those values
            # match the craziest parts of the spellcard
            if arg == 0:
                self.variables[9] = 40 #TODO: is that all?
                self.variables[7] = 2. #TODO: check value. is that all?
            else:
                #TODO: check
                self.variables[6] = self._game.prng.rand_double() * (self._game.width - 64.) + 32.
                self.variables[7] = self._game.prng.rand_double() * (self._game.width / 2. - 64.) + 32.
        else:
            logger.warn("Unimplemented special function %d!", function)


    @instruction(123)
    def skip_frames(self, frames):
        #TODO: is that all?
        self.frame += self._getval(frames)


    @instruction(124)
    def drop_specific_bonus(self, _type):
        #TODO: if _type < 0, “drop” an bullet animation instead of a bonus (never used).
        self._game.drop_bonus(self._enemy.x, self._enemy.y, _type)


    @instruction(126)
    def set_remaining_lives(self, lives):
        self._enemy.remaining_lives = lives


    @instruction(128)
    def interrupt(self, event):
        self._enemy.anmrunner.interrupt(event)


    @instruction(129)
    def interrupt_aux(self, number, event):
        self._enemy.aux_anm[number].anmrunner.interrupt(event)


    @instruction(132)
    def set_visible(self, value):
        self._enemy.visible = not bool(value)


    @instruction(131)
    def set_difficulty_coeffs(self, speed_a, speed_b, nb_a, nb_b, shots_a, shots_b):
        self._enemy.difficulty_coeffs = (speed_a, speed_b, nb_a, nb_b, shots_a, shots_b)

