from itertools import izip, chain, repeat


class AnmWrapper(object):
    def __init__(self, anm_files, offsets=()):
        self.scripts = {}
        self.sprites = {}

        for anm, offset in izip(anm_files, chain(offsets, repeat(0))):
            for script_id, script in anm.scripts.iteritems():
                self.scripts[script_id + offset] = (anm, script) #TODO: check
            for sprite_id, sprite in anm.sprites.iteritems():
                self.sprites[sprite_id + offset] = (anm, sprite)


    def get_sprite(self, sprite_index):
        return self.sprites[sprite_index]


    def get_script(self, script_index):
        return self.scripts[script_index]

