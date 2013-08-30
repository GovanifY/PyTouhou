# -*- encoding: utf-8 -*-

import os
import sys
from distutils.core import setup
from distutils.extension import Extension
from subprocess import check_output

# Cython is needed
try:
    from Cython.Build import cythonize
except ImportError:
    print('You don’t seem to have Cython installed. Please get a '
          'copy from http://www.cython.org/ and install it.')
    sys.exit(1)


COMMAND = 'pkg-config'
SDL_LIBRARIES = ['sdl2', 'SDL2_image', 'SDL2_mixer']

packages = []
extension_names = []
extensions = []


def get_arguments(arg, libraries):
    try:
        return check_output([COMMAND, arg] + libraries).split()
    except OSError:
        print('You don’t seem to have pkg-config installed. Please get a copy '
              'from http://pkg-config.freedesktop.org/ and install it.\n'
              'If you prefer to use it from somewhere else, just modify the '
              'setup.py script.')
        sys.exit(1)


for directory, _, files in os.walk('pytouhou'):
    package = directory.replace(os.path.sep, '.')
    packages.append(package)
    for filename in files:
        if filename.endswith('.pyx') or filename.endswith('.py') and not filename == '__init__.py':
            extension_name = '%s.%s' % (package, os.path.splitext(filename)[0])
            extension_names.append(extension_name)
            if extension_name == 'pytouhou.lib.sdl':
                compile_args = get_arguments('--cflags', SDL_LIBRARIES)
                link_args = get_arguments('--libs', SDL_LIBRARIES)
            elif extension_name.startswith('pytouhou.ui.'): #XXX
                compile_args = get_arguments('--cflags', ['gl'])
                link_args = get_arguments('--libs', ['gl'])
            else:
                compile_args = None
                link_args = None
            extensions.append(Extension(extension_name,
                                        [os.path.join(directory, filename)],
                                        extra_compile_args=compile_args,
                                        extra_link_args=link_args))


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
      ext_modules=cythonize(extensions, nthreads=4,
                            compiler_directives={'infer_types': True,
                                                 'infer_types.verbose': True},
                            compile_time_env={'MAX_TEXTURES': 1024,
                                              'USE_GLEW': is_windows}),
      scripts=['eosd', 'anmviewer'],
      **extra)
