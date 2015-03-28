class ItemType:
    def __init__(self, anm, sprite_index, indicator_sprite_index):
        self.anm = anm
        self.sprite = Sprite()
        self.sprite.anm = anm
        self.sprite.texcoords = anm.sprites[sprite_index]
        self.indicator_sprite = Sprite()
        self.indicator_sprite.anm = anm
        self.indicator_sprite.texcoords = anm.sprites[indicator_sprite_index]
