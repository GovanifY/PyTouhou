from pytouhou.lib cimport sdl
from pytouhou.lib.sdl cimport Window

from pytouhou.lib.opengl cimport \
         (glEnable, glHint, glEnableClientState, GL_TEXTURE_2D, GL_BLEND,
          GL_PERSPECTIVE_CORRECTION_HINT, GL_FOG_HINT, GL_NICEST,
          GL_COLOR_ARRAY, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY,
          glPushDebugGroup, GL_DEBUG_SOURCE_APPLICATION, glPopDebugGroup,
          epoxy_gl_version, epoxy_is_desktop_gl, epoxy_has_gl_extension,
          GL_PRIMITIVE_RESTART, glPrimitiveRestartIndex)


GameRenderer = None


def init(options):
    '''
    Initialize the OpenGL module, and raise if something bad prevents it from
    working.
    '''

    global profile, major, minor, double_buffer, is_legacy, GameRenderer

    flavor = options['flavor']
    assert flavor in ('core', 'es', 'compatibility', 'legacy')
    profile = (sdl.GL_CONTEXT_PROFILE_CORE if flavor == 'core' else
               sdl.GL_CONTEXT_PROFILE_ES if flavor == 'es' else
               sdl.GL_CONTEXT_PROFILE_COMPATIBILITY)

    version = str(options['version'])
    assert len(version) == 3 and version[1] == '.'
    major = int(version[0])
    minor = int(version[2])

    maybe_double_buffer = options['double-buffer']
    double_buffer = maybe_double_buffer if maybe_double_buffer is not None else -1

    is_legacy = flavor == 'legacy'
    is_gles = flavor == 'es'

    #TODO: check for framebuffer/renderbuffer support.

    from pytouhou.ui.opengl.gamerenderer import GameRenderer


def discover_features():
    '''Discover which features are supported by our context.'''

    global use_debug_group, use_vao, use_primitive_restart, shader_header

    version = epoxy_gl_version()
    is_desktop = epoxy_is_desktop_gl()

    use_debug_group = (is_desktop and version >= 43) or epoxy_has_gl_extension('GL_KHR_debug')
    use_vao = (is_desktop and version >= 30) or epoxy_has_gl_extension('GL_ARB_vertex_array_object')
    use_primitive_restart = (is_desktop and version >= 31)

    if is_desktop:
        # gl_FragColor isn’t supported anymore starting with GLSL 4.2.
        if version >= 42:
            version = 41
        try:
            glsl_version = {20: 110, 21: 120, 30: 130, 31: 140, 32: 150}[version]
        except KeyError:
            assert version >= 33
            glsl_version = version * 10
        shader_header = '#version %d\n\n' % glsl_version
    else:
        # The attribute keyword isn’t supported past GLSL ES 3.0.
        if version >= 30:
            version = 20
        glsl_version = {20: '100', 30: '300 es'}[version]
        shader_header = '#version %s\n\nprecision highp float;\n\n' % glsl_version


def create_window(title, x, y, width, height):
    '''Create a window (using SDL) and an OpenGL context.'''

    sdl.gl_set_attribute(sdl.GL_CONTEXT_PROFILE_MASK, profile)
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

    discover_features()

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

    if use_primitive_restart:
        glEnable(GL_PRIMITIVE_RESTART)
        glPrimitiveRestartIndex(0xFFFF);

    if use_debug_group:
        glPopDebugGroup()

    return window
