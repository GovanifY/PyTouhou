# -*- encoding: utf-8 -*-

import os, sys
#import shutil
from distutils.core import setup
from distutils.extension import Extension

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
            extensions.append(Extension('%s.%s' % (package, filename[:-4]),
                                        ['%s/%s' % (directory, filename)]))

#TODO: put eclviewer.py in /usr/bin/ the right way
#shutil.copyfile('eclviewer.py', 'pytouhou/pytouhou')

setup(name='PyTouhou',
      packages=packages,
      ext_modules=extensions,
      #scripts=['pytouhou/pytouhou'],
      cmdclass = {'build_ext': build_ext})
