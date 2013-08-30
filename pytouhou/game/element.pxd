from pytouhou.game.sprite cimport Sprite

cdef class Element:
    cdef public double x, y
    cdef public bint removed
    cdef public Sprite sprite
    cdef public list objects
    cdef public object anmrunner
