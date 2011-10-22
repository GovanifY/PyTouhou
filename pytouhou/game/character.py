class Character(object):
    def __init__(self, anm_wrapper, speed, focused_speed, hitbox_size, graze_hitbox_size):
        self.anm_wrapper = anm_wrapper
        self.speed = speed
        self.focused_speed = focused_speed
        self.hitbox_size = hitbox_size
        self.graze_hitbox_size = graze_hitbox_size
