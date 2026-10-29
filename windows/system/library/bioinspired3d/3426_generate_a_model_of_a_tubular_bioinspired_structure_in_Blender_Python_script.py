# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_tubular_bioinspired_structure_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a tubular bioinspired structure in Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular arrangement
num_tubules = 16  # Total number of tubules
stretch_factor = 1.5  # Factor to stretch tubules
base_radius = 0.08  # Base radius of tubules


def construct_tubule_structure(tubule_count, ellipticity=1.0, radius=0.1):
    # Function to create a cube and arrange tubules in a grid
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dim
    start = -1 + spacing / 2
    
    positions = [(start + (i % grid_dim) * spacing, start + (i // grid_dim) * spacing) for i in range(tubule_count)]
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        
        bool_modifier = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
construct_tubule_structure(num_tubules, stretch_factor, base_radius)
