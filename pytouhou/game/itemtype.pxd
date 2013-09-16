from pytouhou.game.sprite cimport Sprite

cdef class ItemType:
    cdef Sprite sprite, indicator_sprite
    cdef object anm
