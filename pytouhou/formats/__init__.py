"""Touhou games file formats handling.

This package provides modules to handle the various proprietary file formats
used by Touhou games.
"""

class WrongFormatError(Exception):
    pass

class ChecksumError(Exception):
    pass
