# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_generating_a_tubular_bioinspired_material_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for generating a tubular bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

count_tubules = 12
ellipse_ratio = 1.8
tubule_diameter = 0.07

def build_tubule_cube(count, ellipse, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_dim = math.ceil(math.sqrt(count))
    interval = 2 / grid_dim
    offset = -1 + interval / 2

    for i in range(count):
        x = offset + (i % grid_dim) * interval
        y = offset + (i // grid_dim) * interval
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        cylinder = bpy.context.object
        cylinder.scale[0] *= ellipse
        bool_mod = cube_object.modifiers.new(name="Bool_{0}_{1}".format(x, y), type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cylinder
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

build_tubule_cube(count_tubules, ellipse_ratio, tubule_diameter)
