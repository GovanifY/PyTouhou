from pytouhou.utils.matrix cimport Matrix
from .renderer cimport Renderer
from .shader cimport Shader

cdef class GameRenderer(Renderer):
    cdef Matrix game_mvp, interface_mvp, proj
    cdef Shader game_shader, background_shader, interface_shader

    cdef object game, background, background_renderer #XXX
