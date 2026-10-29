# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_Blender_Python_script_that_creates_a_cube_of_tubular_material_think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make Blender Python script that creates a cube of tubular material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define dimensions for the tubule arrangement
total_tubules = 12  # Number of tubules
ellipse_factor = 1.2  # Stretch factor for the tubules
radius_of_tubules = 0.06  # Radius of each tubule

def create_cuboid_with_tubules(tubule_count, ellipticity, radius):
    # Function to create a cube and subtract tubules from it.
    # 1. Create a base cube.
    # 2. Position tubules in a grid format.
    # 3. Use Boolean modifiers for subtraction.
    
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid size and spacing
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Generate positions for tubules
    tubule_positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(tubule_count)]
    
    # Iterate through positions to create tubules
    for position in tubule_positions:
        x, y = position
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= ellipticity  # Apply ellipticity
        
        # Create a Boolean modifier
        bool_mod = base_cube.modifiers.new(name=f"Sub_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule
        
        # Apply the modifier
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Delete the tubule after subtraction
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Create the structure
create_cuboid_with_tubules(total_tubules, ellipse_factor, radius_of_tubules)
