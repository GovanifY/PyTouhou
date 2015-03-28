from pytouhou.utils.matrix cimport Matrix
from pytouhou.game.game cimport Game
from .background cimport BackgroundRenderer
from .renderer cimport Renderer
from .framebuffer cimport Framebuffer
from .shader cimport Shader

cdef class GameRenderer(Renderer):
    cdef Matrix *game_mvp
    cdef Matrix *interface_mvp
    cdef Matrix *proj
    cdef Shader game_shader, background_shader, interface_shader
    cdef Framebuffer framebuffer
    cdef BackgroundRenderer background_renderer
    cdef object background

    cdef bint render_game(self, Game game) except True
    cdef bint render_text(self, dict texts) except True
    cdef bint render_interface(self, interface, game_boss) except True
