# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_generates_a_model_of_a_tubular_porous_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that generates a model of a tubular porous bioinspired structure with noise

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define structure parameters
count_tubules = 20
noise_amplitude = 0.06

def add_tubules(num_tubules, noise):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_pos = -1 + spacing / 2

    positions = [(start_pos + (i % grid_size) * spacing,
                  start_pos + (i // grid_size) * spacing)
                 for i in range(num_tubules)]

    for x, y in positions:
        x += random.uniform(-noise, noise)
        y += random.uniform(-noise, noise)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_mod = base_cube.modifiers.new(name=f"BoolMod_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubules
add_tubules(count_tubules, noise_amplitude)
