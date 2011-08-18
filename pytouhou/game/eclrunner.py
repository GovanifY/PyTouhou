class ECLRunner(object):
    def __init__(self, ecl, sub, frame=0, instruction_pointer=0, implementation=None):
        self.ecl = ecl

        self.counters = {}
        self.implementation = {4: (self.set_counter),
                               2: (self.relative_jump),
                               3: (self.relative_jump_ex)}
        if implementation:
            self.implementation.update(implementation)

        self.sub = sub
        self.frame = frame
        self.instruction_pointer = instruction_pointer


    def set_counter(self, counter_id, count):
        self.counters[counter_id & 0xffff] = count


    def relative_jump(self, frame, instruction_pointer):
        self.frame, self.instruction_pointer = frame, instruction_pointer


    def relative_jump_ex(self, frame, instruction_pointer, counter_id):
        if self.counters[counter_id & 0xffff]:
            self.counters[counter_id & 0xffff] -= 1
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
                if frame <= self.frame:
                    self.instruction_pointer += 1
        except IndexError:
            pass #TODO: script ended, destroy enemy

        self.frame += 1

