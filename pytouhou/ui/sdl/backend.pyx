cimport pytouhou.lib.sdl as sdl
from pytouhou.lib.sdl cimport Window


GameRenderer = None


def init(_):
    global GameRenderer
    from pytouhou.ui.sdl.gamerenderer import GameRenderer


def create_window(title, x, y, width, height, _):
    window = Window(title, x, y, width, height, sdl.WINDOW_SHOWN)
    window.create_renderer(0)
    return window
