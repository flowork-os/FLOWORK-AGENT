# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_script_that_constructs_a_model_of_a_tubular_bioinspired_material_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender script that constructs a model of a tubular bioinspired material with noisy tubule placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular arrangement
num_tubules = 12  # Total tubules in the formation
max_noise = 0.07  # Maximum deviation for noise effect

def generate_tubules(count=12, noise_level=0.07):
    # Constructs a cube with a grid of tubules that have random noise in their placement.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    coords = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(count)]
    
    jittered_coords = [(x + random.uniform(-noise_level, noise_level), y + random.uniform(-noise_level, noise_level)) for x, y in coords]
    
    for x, y in jittered_coords:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule_cylinder = bpy.context.object

        boolean_modifier = cube_object.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule_cylinder

        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)

        bpy.data.objects.remove(tubule_cylinder, do_unlink=True)

# Create the tubular structure
generate_tubules(num_tubules, max_noise)
