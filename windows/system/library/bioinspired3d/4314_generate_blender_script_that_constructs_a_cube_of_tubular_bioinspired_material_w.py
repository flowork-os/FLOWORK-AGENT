# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_that_constructs_a_cube_of_tubular_bioinspired_material_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script that constructs a cube of tubular bioinspired material with layers around each tubule. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for the tubular design
number_of_tubules = 20  # Total number of tubules
layer_thickness_value = 0.03  # Thickness of layer surrounding each tubule

def create_tubular_structure():
    # Constructs a cube with a grid of tubules surrounded by a layer.
    # Add a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid layout for tubules
    grid_count = math.ceil(math.sqrt(number_of_tubules))
    distance = 2 / grid_count
    offset = -1 + distance / 2
    
    # Determine positions for tubules
    tubule_positions = [(offset + (i % grid_count) * distance, 
                         offset + (i // grid_count) * distance) 
                        for i in range(number_of_tubules)]
    
    # List to hold tubule shells for merging
    shell_objects = []
    
    # Create and subtract tubules from the cube
    for x, y in tubule_positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        # Create outer tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Apply Boolean to subtract inner tubule from the cube
        cube_bool_mod = base_cube.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube_bool_mod.operation = 'DIFFERENCE'
        cube_bool_mod.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_bool_mod.name)
        
        # Apply Boolean to create a hollow layer around the inner tubule
        inner_bool_mod = inner_tubule.modifiers.new(name=f"Inner_Bool_{x}_{y}", type='BOOLEAN')
        inner_bool_mod.operation = 'DIFFERENCE'
        inner_bool_mod.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=inner_bool_mod.name)

        # Remove the outer tubule after processing
        bpy.data.objects.remove(outer_tubule, do_unlink=True)

        # Store the processed inner tubule for merging
        shell_objects.append(inner_tubule)
        
    # Merge all tubule shells
    if shell_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for shell in shell_objects:
            shell.select_set(True)
        bpy.context.view_layer.objects.active = shell_objects[0]
        bpy.ops.object.join()
        final_tubule_shell = bpy.context.object
        final_tubule_shell.name = "Tubule_Structure"

# Execute the tubular structure creation
create_tubular_structure()
