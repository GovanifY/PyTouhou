from pytouhou.lib cimport sdl
from pytouhou.lib.sdl cimport Window

from pytouhou.lib.opengl cimport \
         (glEnable, glHint, glEnableClientState, GL_TEXTURE_2D, GL_BLEND,
          GL_PERSPECTIVE_CORRECTION_HINT, GL_FOG_HINT, GL_NICEST,
          GL_COLOR_ARRAY, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY,
          glPushDebugGroup, GL_DEBUG_SOURCE_APPLICATION, glPopDebugGroup)


GameRenderer = None


def init(options):
    global flavor, version, major, minor, double_buffer, is_legacy, use_debug_group, use_vao, shader_header, GameRenderer

    flavor_name = options['flavor']
    assert flavor_name in ('core', 'es', 'compatibility', 'legacy')
    flavor = (sdl.GL_CONTEXT_PROFILE_CORE if flavor_name == 'core' else
              sdl.GL_CONTEXT_PROFILE_ES if flavor_name == 'es' else
              sdl.GL_CONTEXT_PROFILE_COMPATIBILITY)

    version = str(options['version'])
    assert len(version) == 3 and version[1] == '.'
    major = int(version[0])
    minor = int(version[2])

    maybe_double_buffer = options['double-buffer']
    double_buffer = maybe_double_buffer if maybe_double_buffer is not None else -1
    use_debug_group = (major == 4 and minor >= 3) or major > 4
    use_vao = (major == 3 and minor >= 1) or major > 3

    is_legacy = flavor_name == 'legacy'
    is_gles = flavor_name == 'es'

    if not is_gles:
        try:
            glsl_version = {'2.0': 110, '2.1': 120, '3.0': 130, '3.1': 140, '3.2': 150}[version]
        except KeyError:
            assert (major == 3 and minor == 3) or major > 3
            glsl_version = 100 * major + 10 * minor
        shader_header = '#version %d\n' % glsl_version
    else:
        glsl_version = {'2.0': 100, '3.0': 300}[version]
        shader_header = '#version %d\n\nprecision highp float;\n' % glsl_version

    #TODO: check for framebuffer/renderbuffer support.

    from pytouhou.ui.opengl.gamerenderer import GameRenderer


def create_window(title, x, y, width, height):
    sdl.gl_set_attribute(sdl.GL_CONTEXT_PROFILE_MASK, flavor)
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

    if use_debug_group:
        glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "OpenGL initialisation")

    # Initialize OpenGL
    glEnable(GL_BLEND)
    if is_legacy:
        glEnable(GL_TEXTURE_2D)
        glHint(GL_FOG_HINT, GL_NICEST)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glEnableClientState(GL_COLOR_ARRAY)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    if use_debug_group:
        glPopDebugGroup()

    return window
