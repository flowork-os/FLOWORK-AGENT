# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_python_code__make_a_model_of_a_tubular_structure_with_tubule_layer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender python code, make a model of a tubular structure with tubule layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set parameters for the tubular formation
num_tubules = 16  # Number of tubules in the structure
layer_width = 0.05  # Thickness of the layer around each tubule

def generate_tubules():
    # Function to create a cube with a grid of tubules surrounded by a layer.
    # Steps:
    # 1. Create a base cube.
    # 2. Position tubules in a grid layout.
    # 3. Create inner and outer tubules for each grid point.
    # 4. Use Boolean modifiers to subtract inner tubules from the cube.
    # 5. Subtract inner tubule from outer tubule to form the layer.

    # Add a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate the grid dimensions for tubules
    grid_dim = math.ceil(math.sqrt(num_tubules))
    gap = 2 / grid_dim
    offset = -1 + gap / 2
    
    # Determine positions for tubules in the grid
    coordinates = [(offset + (i % grid_dim) * gap,
                    offset + (i // grid_dim) * gap)
                   for i in range(num_tubules)]
    
    # List for storing layer objects
    shell_objects = []
    
    # Loop through positions and subtract cylinders from the cube
    for x, y in coordinates:
        # Create a tubule at the specified position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        # Create a layer at the same position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        
        # Apply Boolean modifier to remove the inner tube from the cube
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Apply Boolean modifier to create the hollow layer around the tubule
        layer_modifier = inner_tube.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        # Remove the outer tube object after subtraction
        bpy.data.objects.remove(outer_tube, do_unlink=True)

        # Store the processed inner tube for merging
        shell_objects.append(inner_tube)
        
    # Combine all layer objects into one
    if shell_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in shell_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = shell_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Layer_Shell"

# Execute the tubule creation function
generate_tubules()
