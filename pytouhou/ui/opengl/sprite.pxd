from pytouhou.game.sprite cimport Sprite

cdef struct RenderingData:
    float pos[12]
    float left, right, bottom, top
    unsigned char color[4]
    long key

cdef RenderingData* get_sprite_rendering_data(Sprite sprite) nogil
cdef void render_sprite(Sprite sprite) nogil
