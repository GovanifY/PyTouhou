class BulletType(object):
    def __init__(self, anm_wrapper, anim_index, cancel_anim_index,
                 launch_anim2_index, launch_anim4_index, launch_anim8_index,
                 hitbox_size,
                 launch_anim_penalties=(0.5, 0.4, 1./3.),
                 launch_anim_offsets=(0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 0),
                 type_id=0):
        self.type_id = type_id
        self.anm_wrapper = anm_wrapper
        self.anim_index = anim_index
        self.cancel_anim_index = cancel_anim_index
        self.launch_anim2_index = launch_anim2_index
        self.launch_anim4_index = launch_anim4_index
        self.launch_anim8_index = launch_anim8_index
        self.hitbox_size = hitbox_size
        self.launch_anim_penalties = launch_anim_penalties
        self.launch_anim_offsets = launch_anim_offsets

