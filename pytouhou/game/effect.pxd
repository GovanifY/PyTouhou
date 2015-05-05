from pytouhou.game.element cimport Element

cdef class Effect(Element):
    cpdef update(self)
