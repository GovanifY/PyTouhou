from pytouhou.utils.matrix cimport Matrix
from .background cimport BackgroundRenderer
from .renderer cimport Renderer, Framebuffer
from .shader cimport Shader

cdef class GameRenderer(Renderer):
    cdef Matrix game_mvp, interface_mvp, proj
    cdef Shader game_shader, background_shader, interface_shader, passthrough_shader
    cdef Framebuffer framebuffer
    cdef BackgroundRenderer background_renderer

    cdef void load_background(self, background)
    cdef void start(self, game)
    cdef void render(self, game)
    cdef void render_game(self, game)
    cdef void render_text(self, texts)
    cdef void render_interface(self, interface, game_boss)
