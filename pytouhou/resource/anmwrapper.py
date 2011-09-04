class AnmWrapper(object):
    def __init__(self, anm_files):
        self.anm_files = list(anm_files)


    def get_sprite(self, sprite_index):
        for anm in self.anm_files:
            if sprite_index in anm.sprites:
                return anm, anm.sprites[sprite_index]
        raise IndexError


    def get_script(self, script_index):
        for anm in self.anm_files:
            if script_index in anm.scripts:
                return anm, anm.scripts[script_index]
        raise IndexError
