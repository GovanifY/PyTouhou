# -*- encoding: utf-8 -*-

import os, sys
from distutils.core import setup
from distutils.extension import Extension
from distutils.command.build_scripts import build_scripts
from distutils.dep_util import newer
from distutils import log
from subprocess import check_output

# Cython is needed
try:
    from Cython.Distutils import build_ext
except ImportError:
    print('You don’t seem to have Cython installed. Please get a '
          'copy from www.cython.org and install it')
    sys.exit(1)


COMMAND = 'pkg-config'
LIBRARIES = ['sdl2', 'SDL2_image', 'SDL2_mixer']

packages = []
extension_names = []
extensions = []



# The installed script shouldn't call pyximport, strip references to it
class BuildScripts(build_scripts):
    def copy_scripts(self):
        self.mkpath('scripts')
        for script in (os.path.basename(script) for script in self.scripts):
            outfile = os.path.join('scripts', script)
            if not self.force and not newer(script, outfile):
                log.debug("not copying %s (up-to-date)", script)
            elif not self.dry_run:
                with open(script, 'r') as file, open(outfile, 'w') as out:
                    for line in file:
                        if not 'pyximport' in line:
                            out.write(line)

        build_scripts.copy_scripts(self)



for directory, _, files in os.walk('pytouhou'):
    package = directory.replace(os.path.sep, '.')
    packages.append(package)
    for filename in files:
        if filename.endswith('.pyx'):
            extension_name = '%s.%s' % (package, os.path.splitext(filename)[0])
            extension_names.append(extension_name)
            if extension_name == 'pytouhou.lib.sdl':
                compile_args = check_output([COMMAND, '--cflags'] + LIBRARIES).split()
                link_args = check_output([COMMAND, '--libs'] + LIBRARIES).split()
            elif extension_name.startswith('pytouhou.ui.'): #XXX
                compile_args = check_output([COMMAND, '--cflags', 'gl']).split()
                link_args = check_output([COMMAND, '--libs', 'gl']).split()
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
    extra = {}
else:
    extra = {
             'options': {'build_exe': {'includes': extension_names}},
             'executables': [Executable(script='scripts/eosd', base='Win32GUI')]
            }



setup(name='PyTouhou',
      version="0.1",
      author='Thibaut Girka',
      author_email='thib@sitedethib.com',
      url='http://hg.sitedethib.com/touhou/',
      license='GPLv3',
      packages=packages,
      ext_modules=extensions,
      scripts=['scripts/eosd', 'scripts/anmviewer'],
      cmdclass={'build_ext': build_ext,
                'build_scripts': BuildScripts},
      **extra
     )

