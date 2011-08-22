class MetaRegistry(type):
    def __new__(mcs, name, bases, classdict):
        instruction_handlers = {}
        for item in classdict.itervalues():
            try:
                instruction_ids = item._instruction_ids
            except AttributeError:
                pass
            else:
                for id_ in instruction_ids:
                    instruction_handlers[id_] = item
        classdict['_handlers'] = instruction_handlers
        return type.__new__(mcs, name, bases, classdict)



def instruction(instruction_id):
    def _decorator(func):
        if not hasattr(func, '_instruction_ids'):
            func._instruction_ids = set()
        func._instruction_ids.add(instruction_id)
        return func
    return _decorator



class ECLRunner(object):
    __metaclass__ = MetaRegistry
    __slots__ = ('_ecl', '_enemy', '_game_state', 'variables', 'sub', 'frame',
                 'instruction_pointer', 'stack')

    def __init__(self, ecl, sub, enemy, game_state):
        # Things not supposed to change
        self._ecl = ecl
        self._enemy = enemy
        self._game_state = game_state

        # Things supposed to change (and be put in the stack)
        self.variables = [0,  0,  0,  0,
                          0., 0., 0., 0.,
                          0,  0,  0,  0]
        self.sub = sub
        self.frame = 0
        self.instruction_pointer = 0

        self.stack = []


    def run_iteration(self):
        # First, if enemy is dead, return
        if self._enemy._removed:
            return False

        # Then, check for callbacks
        #TODO

        # Now, process script
        frame = self.frame
        while True:
            try:
                frame, instr_type, rank_mask, param_mask, args = self._ecl.subs[self.sub][self.instruction_pointer]
            except IndexError:
                return False

            #TODO: skip bad ranks

            if frame > self.frame:
                break
            else:
                self.instruction_pointer += 1
            if frame == self.frame:
                try:
                    callback = self._handlers[instr_type]
                except KeyError:
                    print('Warning: unhandled opcode %d!' % instr_type) #TODO
                else:
                    callback(self, *args)

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
                player = self._enemy.select_player(self._game_state.players)
                return player.x
            elif value == -10019:
                player = self._enemy.select_player(self._game_state.players)
                return player.y
            elif value == -10021:
                player = self._enemy.select_player(self._game_state.players)
                return self._enemy.get_player_angle(player)
            elif value == -10022:
                return self._enemy.frame
            elif value == -10024:
                return self._enemy.life
            raise NotImplementedError #TODO
        else:
            return value


    def _setval(self, variable_id, value):
        if -10012 <= variable_id <= -10001:
            self.variables[int(-10001-variable_id)] = value
        elif -10025 <= variable_id <= -10013:
            if value == -10015:
                self._enemy.x = value
            elif value == -10016:
                self._enemy.y = value
            elif value == -10017:
                self._enemy.z = value
            elif value == -10022:
                self._enemy.frame = value
            elif value == -10024:
                self._enemy.life = value
            raise IndexError #TODO: proper exception
        else:
            raise IndexError #TODO: proper exception


    @instruction(1)
    def destroy(self, arg):
        #TODO: arg?
        self._enemy._removed = True


    @instruction(2)
    def relative_jump(self, frame, instruction_pointer):
        self.frame, self.instruction_pointer = frame, instruction_pointer


    @instruction(3)
    def relative_jump_ex(self, frame, instruction_pointer, variable_id):
        counter_value = self._getval(variable_id)
        if counter_value:
            self._setval(variable_id, counter_value - 1)
            self.frame, self.instruction_pointer = frame, instruction_pointer


    @instruction(4)
    @instruction(5)
    def set_variable(self, variable_id, value):
        self._setval(variable_id, self._getval(value))


    @instruction(6)
    def set_random_int(self, variable_id, maxval):
        self._setval(variable_id, int(self._getval(maxval) * self._game_state.prng.rand_double()))


    @instruction(8)
    def set_random_float(self, variable_id, maxval):
        self._setval(variable_id, self._getval(maxval) * self._game_state.prng.rand_double())


    @instruction(20)
    def add(self, variable_id, a, b):
        #TODO: int vs float thing
        self._setval(variable_id, self._getval(a) + self._getval(b))


    @instruction(21)
    def substract(self, variable_id, a, b):
        #TODO: int vs float thing
        self._setval(variable_id, self._getval(a) - self._getval(b))


    @instruction(35)
    def call(self, sub, param1, param2):
        self.stack.append((self.sub, self.frame, self.instruction_pointer,
                           self.variables))
        self.sub = sub
        self.frame = 0
        self.instruction_pointer = 0
        self.variables = [param1, 0,  0,  0,
                          param2, 0., 0., 0.,
                          0,      0,  0,  0]


    @instruction(36)
    def ret(self):
        self.sub, self.frame, self.instruction_pointer, self.variables = self.stack.pop()


    @instruction(39)
    def call_if_equal(self, sub, param1, param2, a, b):
        if self._getval(a) == self._getval(b):
            self.call(sub, param1, param2)


    @instruction(43)
    def set_pos(self, x, y, z):
        self._enemy.set_pos(x, y, z)


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


    @instruction(51)
    def target_player(self, unknown, speed):
        #TODO: unknown
        self._enemy.speed = speed
        self._enemy.angle = self._enemy.get_player_angle(self._enemy.select_player(self._game_state.players))


    @instruction(57)
    def move_to(self, duration, x, y, z):
        self._enemy.move_to(duration, x, y, z)


    @instruction(65)
    def set_screen_box(self, xmin, ymin, xmax, ymax):
        self._enemy.screen_box = xmin, ymin, xmax, ymax


    @instruction(66)
    def clear_screen_box(self):
        self._enemy.screen_box = None


    @instruction(77)
    def set_bullet_interval(self, value):
        self._enemy.bullet_launch_interval = value


    @instruction(78)
    def set_delay_attack(self):
        self._enemy.delay_attack = True


    @instruction(79)
    def set_no_delay_attack(self):
        self._enemy.delay_attack = False


    @instruction(81)
    def set_bullet_launch_offset(self, x, y, z):
        self._enemy.bullet_launch_offset = (x, y)


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


    @instruction(103)
    def set_hitbox(self, width, height, depth):
        self._enemy.hitbox = (width, height)


    @instruction(105)
    def set_vulnerable(self, vulnerable):
        self._enemy.vulnerable = bool(vulnerable & 1)


    @instruction(108)
    def set_death_callback(self, sub):
        self._enemy.death_callback = sub


    @instruction(109)
    def memory_write(self, value, index):
        #TODO
        #XXX: this is a hack to display bosses although we don't handle MSG :)
        if index == 0:
            self.sub = value
            self.frame = 0
            self.instruction_pointer = 0


    @instruction(113)
    def set_low_life_trigger(self, value):
        self._enemy.low_life_trigger = value


    @instruction(114)
    def set_low_life_callback(self, sub):
        self._enemy.low_life_callback = sub


    @instruction(115)
    def set_timeout(self, timeout):
        self._enemy.timeout = timeout


    @instruction(126)
    def set_remaining_lives(self, lives):
        self._enemy.remaining_lives = lives

