# -*- encoding: utf-8 -*-

import os
import sys
from distutils.core import setup
from distutils.extension import Extension
from subprocess import check_output, CalledProcessError

# Cython is needed
try:
    from Cython.Build import cythonize
except ImportError:
    print('You don’t seem to have Cython installed. Please get a '
          'copy from http://www.cython.org/ and install it.')
    sys.exit(1)


COMMAND = 'pkg-config'
SDL_LIBRARIES = ['sdl2', 'SDL2_image', 'SDL2_mixer', 'SDL2_ttf']
GL_LIBRARIES = ['gl']

packages = []
extension_names = []
extensions = []

debug = False  # True to generate HTML annotations and display infered types.
anmviewer = False  # It’s currently broken anyway.


# Check for gl.pc, and don’t compile the OpenGL backend if it isn’t present.
try:
    check_output([COMMAND] + GL_LIBRARIES)
except CalledProcessError:
    use_opengl = False
else:
    use_opengl = True


def get_arguments(arg, libraries):
    try:
        return check_output([COMMAND, arg] + libraries).split()
    except CalledProcessError:
        # The error has already been displayed, just exit.
        sys.exit(1)
    except OSError:
        print('You don’t seem to have pkg-config installed. Please get a copy '
              'from http://pkg-config.freedesktop.org/ and install it.\n'
              'If you prefer to use it from somewhere else, just modify the '
              'setup.py script.')
        sys.exit(1)


try:
    sdl_args = {'extra_compile_args': get_arguments('--cflags', SDL_LIBRARIES),
                'extra_link_args': get_arguments('--libs', SDL_LIBRARIES)}

    if use_opengl:
        opengl_args = {'extra_compile_args': get_arguments('--cflags', GL_LIBRARIES + SDL_LIBRARIES),
                       'extra_link_args': get_arguments('--libs', GL_LIBRARIES + SDL_LIBRARIES)}
except CalledProcessError:
    # The error has already been displayed, just exit.
    sys.exit(1)
except OSError:
    # pkg-config is needed too.
    print('You don’t seem to have pkg-config installed. Please get a copy '
          'from http://pkg-config.freedesktop.org/ and install it.\n'
          'If you prefer to use it from somewhere else, just modify the '
          'setup.py script.')
    sys.exit(1)


for directory, _, files in os.walk('pytouhou'):
    package = directory.replace(os.path.sep, '.')
    packages.append(package)
    if package not in ('pytouhou.formats', 'pytouhou.game', 'pytouhou.lib', 'pytouhou.utils') and not package.startswith('pytouhou.ui'):
        continue
    if package == 'pytouhou.ui' or package == 'pytouhou.ui.sdl':
        package_args = sdl_args
    elif package == 'pytouhou.ui.opengl':
        package_args = opengl_args
    else:
        package_args = {}
    for filename in files:
        if (filename.endswith('.pyx') or filename.endswith('.py') and
                not filename == '__init__.py'):
            extension_name = '%s.%s' % (package, os.path.splitext(filename)[0])
            extension_names.append(extension_name)
            if extension_name == 'pytouhou.lib.sdl':
                compile_args = sdl_args
            elif extension_name == 'pytouhou.ui.window' and use_opengl:
                compile_args = opengl_args
            elif extension_name == 'pytouhou.ui.anmrenderer' and not anmviewer:
                continue
            elif package == 'pytouhou.formats' and extension_name != 'pytouhou.formats.anm0':
                continue
            else:
                compile_args = package_args
            extensions.append(Extension(extension_name,
                                        [os.path.join(directory, filename)],
                                        **compile_args))


# TODO: find a less-intrusive, cleaner way to do this...
try:
    from cx_Freeze import setup, Executable
except ImportError:
    is_windows = False
    extra = {}
else:
    is_windows = True
    extra = {'options': {'build_exe': {'includes': extension_names}},
             'executables': [Executable(script='eosd', base='Win32GUI')]}


setup(name='PyTouhou',
      version='0.1',
      author='Thibaut Girka',
      author_email='thib@sitedethib.com',
      url='http://pytouhou.linkmauve.fr/',
      license='GPLv3',
      packages=packages,
      ext_modules=cythonize(extensions, nthreads=4, annotate=debug,
                            compiler_directives={'infer_types': True,
                                                 'infer_types.verbose': debug,
                                                 'profile': debug},
                            compile_time_env={'MAX_TEXTURES': 128,
                                              'MAX_ELEMENTS': 640 * 4 * 3,
                                              'MAX_CHANNELS': 26,
                                              'USE_OPENGL': use_opengl,
                                              'USE_GLEW': is_windows}),
      scripts=['eosd'] + (['anmviewer'] if anmviewer else []),
      **extra)
