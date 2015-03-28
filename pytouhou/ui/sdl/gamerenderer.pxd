from pytouhou.game.game cimport Game
from .texture cimport TextureManager, FontManager
from .sprite cimport get_sprite_rendering_data
from pytouhou.ui.window cimport Window

cdef class GameRenderer:
    cdef Window window
    cdef TextureManager texture_manager
    cdef FontManager font_manager
    cdef long x, y, width, height

    cdef public size #XXX

    cdef bint render_game(self, Game game) except True
    cdef bint render_text(self, texts) except True
    cdef bint render_interface(self, interface, game_boss) except True
