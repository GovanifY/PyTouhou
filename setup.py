# -*- encoding: utf-8 -*-

import os, sys
from distutils.core import setup
from distutils.extension import Extension
from distutils.command.build_scripts import build_scripts
from distutils.dep_util import newer
from distutils import log


# Cython is needed
try:
    from Cython.Distutils import build_ext
except ImportError:
    print('You don’t seem to have Cython installed. Please get a '
          'copy from www.cython.org and install it')
    sys.exit(1)


# The installed script shouldn't call pyximport, strip references to it
class BuildScripts(build_scripts):
    def copy_scripts(self):
        for script in (os.path.basename(script) for script in self.scripts):
            outfile = os.path.join('scripts', script)
            if not self.force and not newer(script, outfile):
                log.debug("not copying %s (up-to-date)", script)
            elif not self.dry_run:
                with open(script, 'r') as file, open(outfile, 'w') as out:
                    for line in file:
                        if not 'pyximport' in line:
                            out.write(line)

        orig_build_scripts.copy_scripts(self)


packages = []
extensions = []

for directory, _, files in os.walk('pytouhou'):
    package = directory.replace(os.path.sep, '.')
    packages.append(package)
    for filename in files:
        if filename.endswith('.pyx'):
            extension_name = '%s.%s' % (package, os.path.splitext(filename)[0])
            extensions.append(Extension(extension_name,
                                        [os.path.join(directory, filename)]))



setup(name='PyTouhou',
      author='Thibaut Girka',
      author_email='thib@sitedethib.com',
      url='http://hg.sitedethib.com/touhou/',
      license='GPLv3',
      packages=packages,
      ext_modules=extensions,
      scripts=['scripts/eosd'],
      cmdclass={'build_ext': build_ext,
                'build_scripts': BuildScripts}
     )

