from pytouhou.lib cimport sdl
from pytouhou.lib.sdl cimport Window

from pytouhou.lib.opengl cimport \
         (glEnable, glHint, glEnableClientState, GL_TEXTURE_2D, GL_BLEND,
          GL_PERSPECTIVE_CORRECTION_HINT, GL_FOG_HINT, GL_NICEST,
          GL_COLOR_ARRAY, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY)


GameRenderer = None


def init(options):
    global flavor, version, major, minor, double_buffer, is_legacy, GameRenderer

    flavor = options['flavor']
    assert flavor in ('core', 'es', 'compatibility', 'legacy')

    version = options['version']
    major = int(version)
    minor = <int>(version * 10) % 10

    maybe_double_buffer = options['double-buffer']
    double_buffer = maybe_double_buffer if maybe_double_buffer is not None else -1

    is_legacy = flavor == 'legacy'

    #TODO: check for framebuffer/renderbuffer support.

    from pytouhou.ui.opengl.gamerenderer import GameRenderer


def create_window(title, x, y, width, height):
    sdl.gl_set_attribute(sdl.GL_CONTEXT_MAJOR_VERSION, major)
    sdl.gl_set_attribute(sdl.GL_CONTEXT_MINOR_VERSION, minor)
    sdl.gl_set_attribute(sdl.GL_DEPTH_SIZE, 24)
    if double_buffer >= 0:
        sdl.gl_set_attribute(sdl.GL_DOUBLEBUFFER, double_buffer)

    flags = sdl.WINDOW_SHOWN | sdl.WINDOW_OPENGL

    #TODO: legacy can support one of the framebuffer extensions.
    if not is_legacy:
        flags |= sdl.WINDOW_RESIZABLE

    window = Window(title, x, y, width, height, flags)
    window.gl_create_context()

    # Initialize OpenGL
    glEnable(GL_BLEND)
    if is_legacy:
        glEnable(GL_TEXTURE_2D)
        glHint(GL_FOG_HINT, GL_NICEST)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glEnableClientState(GL_COLOR_ARRAY)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    return window
