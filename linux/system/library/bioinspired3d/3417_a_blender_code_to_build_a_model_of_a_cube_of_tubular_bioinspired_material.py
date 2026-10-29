# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_build_a_model_of_a_cube_of_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to build a model of a cube of tubular bioinspired material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure settings
total_tubules = 25  # Number of tubules
ellipse_factor = 1.2  # Stretch factor
radius_of_tubules = 0.06  # Radius of each tubule


def create_tubule_grid(total_tubules, ellipse_factor=1.0, radius_of_tubules=0.1):
    # This function creates a cube and subtracts tubules from it.
    # Workflow:
    # 1. Create a base cube.
    # 2. Compute positions for tubules.
    # 3. Subtract tubules using Boolean operations.
    
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid layout
    grid_size = math.ceil(math.sqrt(total_tubules))
    distance = 2 / grid_size
    start_position = -1 + distance / 2
    
    # Calculate positions for the tubules
    positions = [(start_position + (i % grid_size) * distance,
                  start_position + (i // grid_size) * distance)
                 for i in range(total_tubules)]
    
    # Subtract each tubule from the cube
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_tubules, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= ellipse_factor
        
        # Create a Boolean modifier
        bool_mod = base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Remove the tubule object
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Generate the grid of tubules
create_tubule_grid(total_tubules, ellipse_factor, radius_of_tubules)
