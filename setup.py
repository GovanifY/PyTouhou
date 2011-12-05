# -*- encoding: utf-8 -*-

import os, sys
from distutils.core import setup
from distutils.extension import Extension


# Cython is needed
try:
    from Cython.Distutils import build_ext
except ImportError:
    print('You don’t seem to have Cython installed. Please get a '
          'copy from www.cython.org and install it')
    sys.exit(1)


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
      cmdclass = {'build_ext': build_ext}
     )

