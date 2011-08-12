from struct import unpack


class ECLRunner(object):
    def __init__(self, ecl, sub, frame=0, instruction_pointer=0, implementation=None):
        self.ecl = ecl

        self.labels = {}
        self.implementation = {4: ('HHI', self.set_label),
                               3: ('IHHHH', self.goto)}
        if implementation:
            self.implementation.update(implementation)

        self.sub = sub
        self.frame = frame
        self.instruction_pointer = instruction_pointer


    def set_label(self, label, unknown, count):
        assert unknown == 0xffff
        self.labels[label] = (self.sub, self.instruction_pointer, count)


    def goto(self, frame, unknown1, unknown2, label, unknown3):
        try:
            sub, instruction_pointer, count = self.labels[label]
        except KeyError:
            pass
        else:
            count -= 1
            if count:
                self.labels[label] = sub, instruction_pointer, count
            else:
                del self.labels[label]
            self.frame = frame
            self.sub, self.instruction_pointer = sub, instruction_pointer


    def update(self):
        frame = self.frame
        try:
            while frame <= self.frame:
                frame, instr_type, rank_mask, param_mask, args = self.ecl.subs[self.sub][self.instruction_pointer]

                if frame == self.frame:
                    try:
                        format, callback = self.implementation[instr_type]
                    except KeyError:
                        print('Warning: unhandled opcode %d!' % instr_type) #TODO
                    else:
                        callback(*unpack('<' + format, args))
                if frame <= self.frame:
                    self.instruction_pointer += 1
        except IndexError:
            pass #TODO: script ended, destroy enemy

        self.frame += 1

