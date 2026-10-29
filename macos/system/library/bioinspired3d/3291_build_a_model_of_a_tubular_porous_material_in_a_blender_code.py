# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_tubular_porous_material_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a tubular porous material in a blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubes in the structure
num_tubes = 16

# Function to create a grid of cylindrical tubes

def build_tube_grid():
    # Step 1: Create a base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Step 2: Determine grid layout for tubes
    grid_dim = math.ceil(math.sqrt(num_tubes))
    tube_spacing = 2 / grid_dim
    offset = -1 + tube_spacing / 2
    
    # Step 3: Calculate positions for the tubes
    tube_positions = [(offset + (i % grid_dim) * tube_spacing,
                       offset + (i // grid_dim) * tube_spacing)
                      for i in range(num_tubes)]
    
    # Step 4: Subtract tubes from the cube
    for pos_x, pos_y in tube_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        tube = bpy.context.object
        
        # Create boolean modifier for subtraction
        bool_mod = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tube
        
        # Apply the boolean operation
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Clean up the tube object
        bpy.data.objects.remove(tube, do_unlink=True)

# Execute tube grid creation
build_tube_grid()
