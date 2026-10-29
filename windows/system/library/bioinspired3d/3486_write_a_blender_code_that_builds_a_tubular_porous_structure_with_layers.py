# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_blender_code_that_builds_a_tubular_porous_structure_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a blender code that builds a tubular porous structure with layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular arrangement
number_of_tubules = 16  # Total tubules in the structure
layer_width = 0.05  # Thickness of the layer around each tubule

def generate_tubules():
    # Function to create a grid of tubules within a cube.
    # Steps:
    # 1. Create a cube.
    # 2. Position tubules in a grid.
    # 3. Create inner and outer tubules for each grid position.
    # 4. Use Boolean modifiers to cut inner tubules from the cube.
    # 5. Create a hollow layer around each tubule.

    # Initialize the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Determine grid size for tubules
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    grid_spacing = 2 / grid_dimension
    offset = -1 + grid_spacing / 2
    
    # Calculate positions for tubules
    positions = [(offset + (i % grid_dimension) * grid_spacing, 
                  offset + (i // grid_dimension) * grid_spacing) 
                 for i in range(number_of_tubules)]
    
    # List to keep track of the tubule shells
    shell_objects = []
    
    for x, y in positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean modifier to subtract inner tubule from cube
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Boolean modifier to create the hollow layer
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        # Remove the outer tubule
        bpy.data.objects.remove(outer_tubule, do_unlink=True)

        # Add processed inner tubule to the shell list
        shell_objects.append(inner_tubule)
    
    # Join all tubule shells into a single object
    if shell_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in shell_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = shell_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Tubule_Shell"

# Execute the tubule generation
generate_tubules()
