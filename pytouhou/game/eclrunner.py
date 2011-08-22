class ECLRunner(object):
    def __init__(self, ecl, sub, frame=0, instruction_pointer=0, implementation=None):
        self.ecl = ecl

        self.variables = [0,  0,  0,  0,
                          0., 0., 0., 0.,
                          0,  0,  0,  0]
        self.sub = sub
        self.frame = frame
        self.instruction_pointer = instruction_pointer

        self.stack = []

        self.implementation = {4: self.set_variable,
                               2: self.relative_jump,
                               3: self.relative_jump_ex,
                               35: self.call,
                               36: self.ret,
                               109: self.memory_write}
        if implementation:
            self.implementation.update(implementation)


    def memory_write(self, value, index):
        #TODO
        #XXX: this is a hack to display bosses although we don't handle MSG :)
        if index == 0:
            self.sub = value
            self.frame = 0
            self.instruction_pointer = 0


    def call(self, sub, param1, param2):
        self.stack.append((self.sub, self.frame, self.instruction_pointer,
                           self.variables))
        self.sub = sub
        self.frame = 0
        self.instruction_pointer = 0
        self.variables = [param1, 0,  0,  0,
                          param2, 0., 0., 0.,
                          0,      0,  0,  0]


    def ret(self):
        self.sub, self.frame, self.instruction_pointer, self.variables = self.stack.pop()



    def set_variable(self, variable_id, value):
        #TODO: -10013 and beyond!
        self.variables[-10000-variable_id] = value


    def relative_jump(self, frame, instruction_pointer):
        self.frame, self.instruction_pointer = frame, instruction_pointer


    def relative_jump_ex(self, frame, instruction_pointer, variable_id):
        if self.variables[-10000-variable_id]:
            self.variables[-10000-variable_id] -= 1
            self.frame, self.instruction_pointer = frame, instruction_pointer


    def update(self):
        frame = self.frame
        try:
            while frame <= self.frame:
                frame, instr_type, rank_mask, param_mask, args = self.ecl.subs[self.sub][self.instruction_pointer]

                if frame == self.frame:
                    try:
                        callback = self.implementation[instr_type]
                    except KeyError:
                        print('Warning: unhandled opcode %d!' % instr_type) #TODO
                    else:
                        callback(*args)
                        frame, instr_type, rank_mask, param_mask, args = self.ecl.subs[self.sub][self.instruction_pointer]
                if frame <= self.frame:
                    self.instruction_pointer += 1
        except IndexError:
            pass #TODO: script ended, destroy enemy

        self.frame += 1

