class LaserType:
    def __init__(self, anm, anim_index,
                 launch_sprite_idx=140,
                 launch_anim_offsets=(0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 0)):
        self.anm = anm
        self.anim_index = anim_index
        self.launch_sprite_idx = launch_sprite_idx
        self.launch_anim_offsets = launch_anim_offsets
