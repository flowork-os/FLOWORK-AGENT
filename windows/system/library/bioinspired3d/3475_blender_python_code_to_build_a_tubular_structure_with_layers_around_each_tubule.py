# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_build_a_tubular_structure_with_layers_around_each_tubule" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to build a tubular structure with layers around each tubule

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for creating tubules
number_of_tubules = 9  # Total number of tubules
layer_shell_thickness = 0.07  # Thickness of the surrounding shell

def build_tubule_structure():
    # This function constructs a grid of tubules with a surrounding shell.
    # Outline:
    # 1. Create a base cube.
    # 2. Position the tubules in a grid.
    # 3. Create inner and outer tubules.
    # 4. Apply Boolean modifiers to subtract inner tubules from the cube.
    # 5. Combine the final structure.

    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_object = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_dimension
    start_offset = -1 + spacing / 2
    
    positions = [(start_offset + (i % grid_dimension) * spacing, 
                  start_offset + (i // grid_dimension) * spacing) 
                 for i in range(number_of_tubules)]
    
    tubule_objects = []
    
    for x, y in positions:
        # Create inner tubule
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        # Create outer tubule layer
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_shell_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean modifier to subtract inner tubule from the cube
        cube_modifier = base_object.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_object
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Boolean modifier for the outer layer
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        # Remove the outer tubule
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        tubule_objects.append(inner_tubule)
    
    # Merge all inner tubules into one object
    if tubule_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in tubule_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = tubule_objects[0]
        bpy.ops.object.join()
        final_tubule_shell = bpy.context.object
        final_tubule_shell.name = "Merged_Tubule_Shell"

# Build the tubular structure
build_tubule_structure()
