from pytouhou.game.sprite cimport Sprite

cdef struct RenderingData:
    int x, y, width, height
    float left, right, bottom, top
    unsigned char r, g, b, a
    long blendfunc
    float rotation
    bint flip

cdef RenderingData* get_sprite_rendering_data(Sprite sprite) nogil
cdef void render_sprite(Sprite sprite) nogil
