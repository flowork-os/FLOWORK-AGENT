# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_python_blender_code_create_a_tubular_structure__think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With python blender code create a tubular structure. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

cylinder_count = 20

def build_tubular_grid():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object

    grid_dim = math.ceil(math.sqrt(cylinder_count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    for i in range(cylinder_count):
        x = offset + (i % grid_dim) * spacing
        y = offset + (i // grid_dim) * spacing
        create_and_subtract_cylinder(main_cube, x, y)

def create_and_subtract_cylinder(cube, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    cylinder = bpy.context.object
    bool_mod = cube.modifiers.new(name=f"Cylinder_{x}_{y}", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cylinder

    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(cylinder, do_unlink=True)

build_tubular_grid()
