# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_builds_a_model_of_a_tubular_porous_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that builds a model of a tubular porous bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the number of tubular structures
num_tubules = 16

# Function to generate the tubules within a cube

def build_tubules():
    # Stepwise creation of a cube and tubules
    # 1. Instantiate a cube.
    # 2. Position tubules in a grid layout.
    # 3. Apply Boolean operations to remove tubules from the cube.
    
    # Add a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid dimensions for tubules
    grid_dim = math.ceil(math.sqrt(num_tubules))
    interval = 2 / grid_dim
    initial_offset = -1 + interval / 2
    
    # Calculate positions for each tubule
    tubule_positions = [(initial_offset + (i % grid_dim) * interval,
                         initial_offset + (i // grid_dim) * interval)
                        for i in range(num_tubules)]
    
    # Subtract tubules from the cube
    for pos_x, pos_y in tubule_positions:
        # Add a cylinder at the designated position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object

        # Create and configure Boolean modifier
        bool_mod = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule

        # Apply the modifier to the cube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        # Clean up by removing the tubule
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the tubule generation
build_tubules()
