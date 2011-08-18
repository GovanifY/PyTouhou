class ECLRunner(object):
    def __init__(self, ecl, sub, frame=0, instruction_pointer=0, implementation=None):
        self.ecl = ecl

        self.labels = {}
        self.implementation = {4: (self.set_label),
                               3: (self.goto)}
        if implementation:
            self.implementation.update(implementation)

        self.sub = sub
        self.frame = frame
        self.instruction_pointer = instruction_pointer


    def set_label(self, label, count):
        self.labels[label & 0xffff] = (self.sub, self.instruction_pointer, count)


    def goto(self, frame, instruction_pointer, label):
        try:
            sub, instruction_pointer, count = self.labels[label & 0xffff]
        except KeyError:
            pass
        else:
            count -= 1
            if count:
                self.labels[label & 0xffff] = sub, instruction_pointer, count
            else:
                del self.labels[label & 0xffff]
            self.frame = frame
            self.sub, self.instruction_pointer = sub, instruction_pointer


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

