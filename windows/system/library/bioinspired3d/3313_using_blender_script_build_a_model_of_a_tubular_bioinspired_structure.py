# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_script_build_a_model_of_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender script build a model of a tubular bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Specify the number of cylinders to create
cylinder_count = 25

def setup_tubules():
    # This function sets up the main cube and subtracts tubules from it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(cylinder_count))
    spacing = 2 / grid_dim
    initial_offset = -1 + spacing / 2
    positions = [(initial_offset + (i % grid_dim) * spacing, initial_offset + (i // grid_dim) * spacing) for i in range(cylinder_count)]
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        cylinder = bpy.context.object
        bool_mod = base_cube.modifiers.new(name=f"Sub_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cylinder
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

setup_tubules()
