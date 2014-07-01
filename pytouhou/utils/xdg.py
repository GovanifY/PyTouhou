# -*- encoding: utf-8
"""
This module is based on a rox module (LGPL):

http://cvs.sourceforge.net/viewcvs.py/rox/ROX-Lib2/python/rox/basedir.py?rev=1.9&view=log

The freedesktop.org Base Directory specification provides a way for
applications to locate shared data and configuration:

    http://standards.freedesktop.org/basedir-spec/

(based on version 0.6)

This module can be used to load and save from and to these directories.

Typical usage:

    from rox import basedir
    
    for dir in basedir.load_config_paths('mydomain.org', 'MyProg', 'Options'):
        print "Load settings from", dir

    dir = basedir.save_config_path('mydomain.org', 'MyProg')
    print >>file(os.path.join(dir, 'Options'), 'w'), "foo=2"

Note: see the rox.Options module for a higher-level API for managing options.
"""

import os

_home = os.path.expanduser('~')
xdg_config_home = os.environ.get('XDG_CONFIG_HOME') or \
    os.path.join(_home, '.config')

xdg_config_dirs = [xdg_config_home] + \
    (os.environ.get('XDG_CONFIG_DIRS') or '/etc/xdg').split(':')

xdg_config_dirs = [x for x in xdg_config_dirs if x]


def save_config_path(*resource):
    resource = os.path.join(*resource)
    assert not resource.startswith('/')
    path = os.path.join(xdg_config_home, resource)
    if not os.path.isdir(path):
        os.makedirs(path, 0o700)
    return path


def load_config_paths(*resource):
    resource = os.path.join(*resource)
    for config_dir in xdg_config_dirs:
        path = os.path.join(config_dir, resource)
        if os.path.exists(path):
            yield path
