# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_code__generate_a_model_of_a_tubular_porous_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender code, generate a model of a tubular porous material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of tubular elements in the model
num_tubules = 16

def generate_tubules():
    # This function constructs a cube with a grid of cylindrical tubules.
    # Steps:
    # 1. Create a cube.
    # 2. Arrange tubules in a grid.
    # 3. Apply Boolean modifiers for subtraction.
    
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid layout for the tubules
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Calculate positions for each tubule
    positions = [(offset + (i % grid_size) * spacing, 
                  offset + (i // grid_size) * spacing) 
                 for i in range(num_tubules)]
    
    # Loop through each position to create and subtract tubules
    for x, y in positions:
        # Add a cylinder at the specified location
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object

        # Create a Boolean modifier for the cube
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule

        # Apply the Boolean operation
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Clean up: remove the tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the tubule generation
generate_tubules()
