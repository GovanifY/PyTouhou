class LaserType(object):
    def __init__(self, anm_wrapper, anim_index,
                 launch_anim_offsets=(0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 0)):
        self.anm_wrapper = anm_wrapper
        self.anim_index = anim_index
        self.launch_anim_offsets = launch_anim_offsets
