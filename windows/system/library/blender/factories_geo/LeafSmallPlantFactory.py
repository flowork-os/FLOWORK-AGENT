# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafSmallPlantFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafSmallPlantFactory | Category: factories_geo
# Prompt: A 3D model of a single broad leaf rendered from an elevated perspective, featuring a rounded teardrop-shaped blade with a slightly pointed tip, a subtle central crease along the midrib, and a flat profile with gentle surface undulation, colored in a muted olive green.

import bpy
import numpy as np

SEED = 0
np.random.seed(SEED)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
bpy.context.scene.cursor.location = (0, 0, 0)

def make_leaf(genome=None):
    g = dict(leaf_width=0.5, alpha=0.3, use_wave=True, x_offset=0,
             flip_leaf=False, z_scaling=0, width_rand=0.33)
    if genome:
        g.update(genome)

    bpy.ops.mesh.primitive_circle_add(
        enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.edge_face_add()
    obj = bpy.context.active_object
    n = len(obj.data.vertices) // 2

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.vertices[0].select = True
    obj.data.vertices[-1].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide()

    a = np.linspace(0, np.pi, n)
    if g['flip_leaf']:
        a = a[::-1]
    x = np.sin(a) * (g['leaf_width'] + np.random.randn() * g['width_rand']) + g['x_offset']
    y = -np.cos(0.9 * (a - g['alpha']))
    z = x ** 2 * g['z_scaling']
    full_coords = np.concatenate([
        np.stack([x, y, z], 1),
        np.stack([-x[::-1], y[::-1], z], 1),
        np.array([[0, y[0], 0]]),
    ]).flatten()
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.vertices.foreach_set('co', full_coords)

    if g['use_wave']:
        bpy.ops.object.modifier_add(type='WAVE')
        bpy.context.object.modifiers['Wave'].height = np.random.randn() * 0.3
        bpy.context.object.modifiers['Wave'].width = 0.75 + np.random.randn() * 0.1
        bpy.context.object.modifiers['Wave'].speed = np.random.rand()

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    bpy.context.scene.cursor.location = obj.data.vertices[-1].co
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.location = (0, 0, 0)
    obj.scale *= 0.3
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return obj

make_leaf()
