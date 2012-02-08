class LaserType(object):
    def __init__(self, anm_wrapper, anim_index,
                 launch_anim_offsets=(0, 1, 1, 1, 1, 3, 3, 3, 3, 5, 5, 5, 6, 6, 6, 0)):
        self.anm_wrapper = anm_wrapper
        self.anim_index = anim_index
        self.launch_anim_offsets = launch_anim_offsets
