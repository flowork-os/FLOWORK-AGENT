# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script__build_a_model_of_a_tubular_porous_bioinspired_materia" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script, build a model of a tubular porous bioinspired material with jittered placement think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular formation
num_tubules = 18
noise_range = 0.07

def add_tubules(tubule_quantity, noise_amount):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(tubule_quantity))
    spacing = 2 / grid_dim
    initial_offset = -1 + spacing / 2
    coords = [(initial_offset + (i % grid_dim) * spacing, initial_offset + (i // grid_dim) * spacing) for i in range(tubule_quantity)]
    jittered_coords = [(x + random.uniform(-noise_amount, noise_amount), y + random.uniform(-noise_amount, noise_amount)) for x, y in coords]
    for x, y in jittered_coords:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        cylinder = bpy.context.object
        bool_mod = main_cube.modifiers.new(name="Subtract_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cylinder
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

# Execute tubule addition
add_tubules(num_tubules, noise_range)
