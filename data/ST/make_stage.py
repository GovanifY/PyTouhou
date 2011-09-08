from pytouhou.formats.std import Stage, Model
from pytouhou.formats.anm0 import Animations
from pytouhou.vm.anmrunner import ANMRunner
from pytouhou.game.sprite import Sprite
from pytouhou.resource.anmwrapper import AnmWrapper
from pytouhou.opengl.sprite import get_sprite_rendering_data

ground = Model(quads=[(14, -100.0, -46*3, 0.5, (192+100)*2, 46*3),
                      (0, 192.0 - 40, -46.0, 0.0, 0, 0),
                      (0, 192.0 - 40, -46.0*2, 0.0, 0, 0),
                      (0, 192.0 - 40, -46.0*3, 0.0, 0, 0),
                      (11, -100.0, -46*3, 0.0, 220, 46*3),
                      (11, 192*2+100.0-220, -46*3, 0.0, 220, 46*3),
                      (12, 120.0, -46*3, -0.1, 0, 46*3),
                      (13, 192*2-120-14, -46*3, -0.1, 0, 46*3)])

tree = Model(quads=[(9, 0.0, 0.0, 0.0, 0, 0)])
tree2 = Model(quads=[(10, 0.0, 0.0, 0.0, 0, 0)])

models = [ground, tree, tree2]


instances = [(0, 0.0, -46*3*-1, 0.0),
             (0, 0.0, -46*3*0, 0.0),
             (0, 0.0, -46*3*1, 0.0),
             (0, 0.0, -46*3*2, 0.0),
             (0, 0.0, -46*3*3, 0.0),
             (0, 0.0, -46*3*4, 0.0),
             (0, 0.0, -46*3*5, 0.0),
             (0, 0.0, -46*3*6, 0.0),
             (0, 0.0, -46*3*7, 0.0),
             (0, 0.0, -46*3*8, 0.0),
             #Trees
             (1, 40.0, -46*3*1, -50.0),
             (1, 40.0, -46*3*2, -50.0),
             (1, 40.0, -46*3*3, -50.0),
             (1, 40.0, -46*3*4, -50.0),
             (1, 40.0, -46*3*5, -50.0),
             (1, 40.0, -46*3*6, -50.0),

             (1, 40.0+40, -46*3*1-20, -50.0),
             (1, 40.0+40, -46*3*2-20, -50.0),
             (1, 40.0+40, -46*3*3-20, -50.0),
             (1, 40.0+40, -46*3*4-20, -50.0),
             (1, 40.0+40, -46*3*5-20, -50.0),
             (1, 40.0+40, -46*3*6-20, -50.0),

             (2, 192*2-30-40.0, -46*3*1, -50.0),
             (2, 192*2-30-40.0, -46*3*2, -50.0),
             (2, 192*2-30-40.0, -46*3*3, -50.0),
             (2, 192*2-30-40.0, -46*3*4, -50.0),
             (2, 192*2-30-40.0, -46*3*5, -50.0),
             (2, 192*2-30-40.0, -46*3*6, -50.0),

             (2, 192*2-30-40.0-50.0, -46*3*1-20, -50.0),
             (2, 192*2-30-40.0-50.0, -46*3*2-20, -50.0),
             (2, 192*2-30-40.0-50.0, -46*3*3-20, -50.0),
             (2, 192*2-30-40.0-50.0, -46*3*4-20, -50.0),
             (2, 192*2-30-40.0-50.0, -46*3*5-20, -50.0),
             (2, 192*2-30-40.0-50.0, -46*3*6-20, -50.0)]


# Bounding boxes
anm_wrapper = AnmWrapper([Animations.read(open('stg1bg.anm', 'rb'))])
for model in models:
    vertices = []
    for script_index, ox2, oy2, oz2, width_override, height_override in model.quads:
        sprite = Sprite(width_override, height_override)
        anmrunner = ANMRunner(anm_wrapper, script_index, sprite)
        anmrunner.run_frame()
        key, (vertices2, uvs2, colors2) = get_sprite_rendering_data(sprite)
        vertices.extend((x + ox2, y + oy2, z + oz2) for x, y, z in vertices2)
    xmin, ymin, zmin = min(x for x, y, z in vertices), min(y for x, y, z in vertices), min(z for x, y, z in vertices)
    xmax, ymax, zmax = max(x for x, y, z in vertices), max(y for x, y, z in vertices), max(z for x, y, z in vertices)
    model.bounding_box = (xmin, ymin, zmin, xmax - xmin, ymax - ymin, zmax - zmin)


stage = Stage()
stage.name = 'Test by ThibG'
stage.bgms = ('', 'bgm/th06_15.mid'), ('', ''), ('', ''), ('', '')
stage.models = models
stage.object_instances = instances
stage.script = [(0, 1, (50, 0, 50, 300.0, 800.0)),
                (0, 2, (0.0, 400.0, 0.3)),
                (0, 0, (0.0, 0.0, 0.0)),
                (1600, 0, (0.0, -600.0, 0.0)),
                (6500, 0, (0.0, -600.0, 0.0))]

with open('stage1.std', 'wb') as file:
    stage.write(file)

