# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_generate_a_tubular_porous_bioinspired_material_with_ji" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script generate a tubular porous bioinspired material with jittered placement. think step by step

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubules = 25
noise_value = 0.07

def create_structure(tubules, noise):
    # Function to create a cube and subtract tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubules))
    spacing = 2 / grid_size
    start = -1 + spacing / 2
    
    positions = [(start + (i % grid_size) * spacing,
                  start + (i // grid_size) * spacing)
                 for i in range(tubules)]
    
    jittered_positions = [(x + random.uniform(-noise, noise),
                           y + random.uniform(-noise, noise)) for x, y in positions]
    
    for x, y in jittered_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        boolean_modifier = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the structure
create_structure(num_tubules, noise_value)
