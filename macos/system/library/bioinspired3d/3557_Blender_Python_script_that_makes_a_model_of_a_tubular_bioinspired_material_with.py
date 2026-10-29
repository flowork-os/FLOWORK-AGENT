# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_makes_a_model_of_a_tubular_bioinspired_material_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that makes a model of a tubular bioinspired material with jittered placement

import bpy
import math
import random

# Clear the scene of existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for the tubular structure
num_tubules = 20
noise_level = 0.05

def create_cube_and_tubules(tubule_count, noise):
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    dimension = math.ceil(math.sqrt(tubule_count))
    separation = 2 / dimension
    origin = -1 + separation / 2
    
    # Determine positions for the tubules
    positions = [(origin + (i % dimension) * separation,
                  origin + (i // dimension) * separation) 
                 for i in range(tubule_count)]
    
    # Apply noise to the positions
    modified_positions = [(x + random.uniform(-noise, noise),
                           y + random.uniform(-noise, noise)) for x, y in positions]
    
    # Create and subtract each tubule
    for x, y in modified_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        
        bool_modifier = cube_object.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
create_cube_and_tubules(num_tubules, noise_level)
