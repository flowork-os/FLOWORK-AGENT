# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code_construct_a_tubular_porous_structure__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code construct a tubular porous structure. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
number_of_tubules = 16  # Total number of tubules
stretch_factor = 1.5  # Factor to stretch tubules into ellipses
base_radius = 0.07  # Base radius of the tubules

def construct_tubule_grid(tubule_count, ellipticity=1.0, radius=0.1):
    # Function to create a grid of tubules and subtract them from a cube.
    # Steps:
    # 1. Create a cube as a base object.
    # 2. Calculate positions for tubules in a grid.
    # 3. Subtract tubules from the cube using Boolean modifiers.
    
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid layout for the tubules
    grid_dimension = math.ceil(math.sqrt(tubule_count))
    distance_between = 2 / grid_dimension
    initial_offset = -1 + distance_between / 2
    
    # Calculate positions for each tubule
    tubule_positions = [
        (initial_offset + (i % grid_dimension) * distance_between,
         initial_offset + (i // grid_dimension) * distance_between)
        for i in range(tubule_count)
    ]
    
    # Subtract each tubule from the cube
    for x_pos, y_pos in tubule_positions:
        # Create a cylinder at the specified position
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x_pos, y_pos, 0))
        tubule_obj = bpy.context.object
        tubule_obj.scale[0] *= ellipticity  # Apply ellipticity scaling
        
        # Add and apply a Boolean modifier to the cube
        bool_modifier = base_cube.modifiers.new(name=f"Boolean_{x_pos}_{y_pos}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_obj
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Clean up by removing the cylinder
        bpy.data.objects.remove(tubule_obj, do_unlink=True)

# Create the tubular structure
construct_tubule_grid(number_of_tubules, stretch_factor, base_radius)
