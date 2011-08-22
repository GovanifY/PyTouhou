class Interpolator(object):
    def __init__(self, values=()):
        self.values = tuple(values)
        self.start_values = tuple(values)
        self.end_values = tuple(values)
        self.start_frame = 0
        self.end_frame = 0
        self._frame = 0


    def set_interpolation_start(self, frame, values):
        self.start_values = tuple(values)
        self.start_frame = frame


    def set_interpolation_end(self, frame, values):
        self.end_values = tuple(values)
        self.end_frame = frame


    def set_interpolation_end_frame(self, end_frame):
        self.end_frame = end_frame


    def set_interpolation_end_values(self, values):
        self.end_values = tuple(values)


    def update(self, frame):
        self._frame = frame
        if frame >= self.end_frame:
            self.values = tuple(self.end_values)
            self.start_values = tuple(self.end_values)
            self.start_frame = frame
            return frame == self.end_frame
        else:
            truc = float(frame - self.start_frame) / float(self.end_frame - self.start_frame)
            self.values = tuple(start_value + truc * (end_value - start_value)
                                for (start_value, end_value) in zip(self.start_values, self.end_values))
            return True

