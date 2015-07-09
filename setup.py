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
GL_LIBRARIES = ['epoxy']

debug = False  # True to generate HTML annotations and display infered types.
anmviewer = False  # It’s currently broken anyway.
nthreads = os.cpu_count()  # How many processes to use for Cython compilation.
compile_everything = False  # Maybe improve running time a bit by wasting a lot
                            # of CPU time during compilation, and disk space.


# Hack to move us to the correct build directory.
os.chdir(os.path.join(os.getcwd(), os.path.dirname(__file__)))


# Hack to prevent `setup.py clean` from compiling Cython files.
if len(sys.argv) > 1 and sys.argv[1] == 'clean':
    import shutil
    shutil.rmtree('build', ignore_errors=True)
    for directory, _, files in os.walk('pytouhou'):
        for filename in files:
            if filename.endswith('.c'):
                os.unlink(os.path.join(directory, filename))
    sys.exit(0)


try:
    sys.argv.remove('--disable-opengl')
except ValueError:
    use_opengl = True
else:
    use_opengl = False


# Check for epoxy.pc, and don’t compile the OpenGL backend if it isn’t present.
if use_opengl:
    try:
        check_output([COMMAND] + GL_LIBRARIES)
    except CalledProcessError:
        print('libepoxy not found.  Please install it or pass --disable-opengl')
        sys.exit(1)
    except OSError:
        # Assume GL is here if we can’t use pkg-config, but display a warning.
        print('You don’t seem to have pkg-config installed. Please get a copy '
              'from http://pkg-config.freedesktop.org/ and install it.\n'
              'Continuing without it, assuming every dependency is available.')


default_libs = {
    'sdl2': '-lSDL2',
    'SDL2_image': '-lSDL2_image',
    'SDL2_mixer': '-lSDL2_mixer',
    'SDL2_ttf': '-lSDL2_ttf',
    'epoxy': '-lepoxy'
}


def get_arguments(arg, libraries):
    try:
        return check_output([COMMAND, arg] + libraries).decode().split()
    except CalledProcessError:
        # The error has already been displayed, just exit.
        sys.exit(1)
    except OSError:
        # We already said to the user pkg-config was suggested.
        if arg == '--cflags':
            return []
        return [default_libs[library] for library in libraries]


sdl_args = {'extra_compile_args': get_arguments('--cflags', SDL_LIBRARIES),
            'extra_link_args': get_arguments('--libs', SDL_LIBRARIES)}

if use_opengl:
    opengl_args = {'extra_compile_args': get_arguments('--cflags', GL_LIBRARIES + SDL_LIBRARIES),
                   'extra_link_args': get_arguments('--libs', GL_LIBRARIES + SDL_LIBRARIES)}


def get_module_hierarchy(directory):
    packages = {}
    allowed_extensions = ('.py', '.pyx', '.pxd')
    pycache = os.path.sep + '__pycache__'
    for directory, _, files in os.walk(directory):
        if directory.endswith(pycache):
            continue
        package_name = directory.replace(os.path.sep, '.')
        package = packages.setdefault(package_name, {})
        for filename in files:
            module_name, file_ext = os.path.splitext(filename)
            if file_ext not in allowed_extensions:
                continue
            package.setdefault(module_name, []).append(file_ext)
        for module_name, extensions in list(package.items()):
            if '.pyx' not in extensions and '.py' not in extensions:
                del package[module_name]
    return packages


def extract_module_types(packages):
    py_modules = []
    ext_modules = []
    for package_name, package in packages.items():
        if package_name in ('pytouhou.ui', 'pytouhou.ui.sdl'):
            package_args = sdl_args
        elif package_name == 'pytouhou.ui.opengl':
            package_args = opengl_args
        else:
            package_args = {}
        for module_name, extensions in package.items():
            fully_qualified_name = '%s.%s' % (package_name, module_name)
            if '.pyx' in extensions or '.pxd' in extensions or compile_everything:
                if fully_qualified_name == 'pytouhou.lib.sdl':
                    compile_args = sdl_args
                else:
                    compile_args = package_args
                ext = 'pyx' if '.pyx' in extensions else 'py'
                source = '%s.%s' % (fully_qualified_name.replace('.', os.path.sep), ext)
                ext_modules.append(Extension(fully_qualified_name,
                                             [source],
                                             **compile_args))
            else:
                py_modules.append(fully_qualified_name)
    return py_modules, ext_modules


packages = get_module_hierarchy('pytouhou')

if not use_opengl:
    del packages['pytouhou.ui.opengl']
    del packages['pytouhou.ui.opengl.shaders']

if not anmviewer:
    del packages['pytouhou.ui']['anmrenderer']

py_modules, ext_modules = extract_module_types(packages)


# OS-specific setuptools options.
try:
    from cx_Freeze import setup, Executable
except ImportError:
    extra = {}
else:
    base = None
    if sys.platform == 'win32':
        nthreads = None  # It seems Windows can’t compile in parallel.
        base = 'Win32GUI'
    extra = {'options': {'build_exe': {'includes': [mod.name for mod in ext_modules] + py_modules}},
             'executables': [Executable(script='scripts/pytouhou', base=base)]}


# Create a link to the data files (for packaging purposes)
current_dir = os.path.dirname(os.path.realpath(__file__))
temp_data_dir = os.path.join(current_dir, 'pytouhou', 'data')
if not os.path.exists(temp_data_dir):
    os.symlink(os.path.join(current_dir, 'data'), temp_data_dir)


setup(name='PyTouhou',
      version=check_output(['hg', 'heads', '.', '-T', '{rev}']).decode(),
      author='Thibaut Girka',
      author_email='thib@sitedethib.com',
      url='http://pytouhou.linkmauve.fr/',
      license='GPLv3',
      py_modules=py_modules,
      ext_modules=cythonize(ext_modules, nthreads=nthreads, annotate=debug,
                            language_level=3,
                            compiler_directives={'infer_types': True,
                                                 'infer_types.verbose': debug,
                                                 'profile': debug},
                            compile_time_env={'MAX_TEXTURES': 128,
                                              'MAX_ELEMENTS': 640 * 4 * 3,
                                              'MAX_SOUNDS': 26,
                                              'USE_OPENGL': use_opengl}),
      scripts=['scripts/pytouhou'] + (['scripts/anmviewer'] if anmviewer else []),
      packages=['pytouhou'],
      package_data={'pytouhou': ['data/menu.glade']},
      **extra)


# Remove the link afterwards
if os.path.exists(temp_data_dir):
    os.unlink(temp_data_dir)
