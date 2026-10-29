# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_blender_python_code_that_generates_a_tubular_porous_bioinspired_structure_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make blender python code that generates a tubular porous bioinspired structure with noise

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Structure parameters
total_tubules = 20
random_noise = 0.07

def build_tubules(total_tubules, random_noise):
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(total_tubules))
    interval = 2 / grid_dim
    offset = -1 + interval / 2

    # Determine positions
    pos_list = [(offset + (i % grid_dim) * interval, offset + (i // grid_dim) * interval) for i in range(total_tubules)]
    jittered_positions = [(x + random.uniform(-random_noise, random_noise), y + random.uniform(-random_noise, random_noise)) for x, y in pos_list]

    # Create and subtract tubules
    for pos in jittered_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos[0], pos[1], 0))
        current_tubule = bpy.context.object
        bool_modifier = base_cube.modifiers.new(name="Bool_{}".format(pos), type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

build_tubules(total_tubules, random_noise)
