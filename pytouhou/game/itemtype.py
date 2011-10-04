from pytouhou.game.sprite import Sprite

class ItemType(object):
    def __init__(self, anm_wrapper, sprite_index, indicator_sprite_index, speed,
                 hitbox_size):
        self.anm_wrapper = anm_wrapper
        self.sprite = Sprite()
        self.sprite.anm, self.sprite.texcoords = anm_wrapper.get_sprite(sprite_index)
        self.indicator_sprite = Sprite()
        self.indicator_sprite.anm, self.indicator_sprite.texcoords = anm_wrapper.get_sprite(indicator_sprite_index)
        self.speed = speed
        self.hitbox_size = hitbox_size
