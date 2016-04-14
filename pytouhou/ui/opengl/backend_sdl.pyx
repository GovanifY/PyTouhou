from .backend cimport profile, major, minor, double_buffer, is_legacy

cimport pytouhou.lib.sdl as sdl


def create_sdl_window(title, x, y, width, height):
    '''Create a window (using SDL) and an OpenGL context.'''

    profile_mask = (sdl.GL_CONTEXT_PROFILE_CORE if profile == 'core' else
                    sdl.GL_CONTEXT_PROFILE_ES if profile == 'es' else
                    sdl.GL_CONTEXT_PROFILE_COMPATIBILITY)

    sdl.gl_set_attribute(sdl.GL_CONTEXT_PROFILE_MASK, profile_mask)
    sdl.gl_set_attribute(sdl.GL_CONTEXT_MAJOR_VERSION, major)
    sdl.gl_set_attribute(sdl.GL_CONTEXT_MINOR_VERSION, minor)
    sdl.gl_set_attribute(sdl.GL_RED_SIZE, 8)
    sdl.gl_set_attribute(sdl.GL_GREEN_SIZE, 8)
    sdl.gl_set_attribute(sdl.GL_BLUE_SIZE, 8)
    sdl.gl_set_attribute(sdl.GL_DEPTH_SIZE, 24 if is_legacy else 0)
    if double_buffer >= 0:
        sdl.gl_set_attribute(sdl.GL_DOUBLEBUFFER, double_buffer)

    flags = sdl.WINDOW_SHOWN | sdl.WINDOW_OPENGL

    # Legacy contexts don’t support our required extensions for scaling.
    if not is_legacy:
        flags |= sdl.WINDOW_RESIZABLE

    window = sdl.Window(title, x, y, width, height, flags)
    #window.create_gl_context()

    #discover_features()

    ## If we can’t use scaling but have previously created a resizable window,
    ## recreate it unresizable.
    #if not use_scaled_rendering and flags & sdl.WINDOW_RESIZABLE:
    #    flags &= ~sdl.WINDOW_RESIZABLE
    #    window = sdl.Window(title, x, y, width, height, flags)
    #    window.create_gl_context()

    return window
