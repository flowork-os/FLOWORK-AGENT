# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_that_builds_a_tubular_bioinspired_material_with_layers_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code that builds a tubular bioinspired material with layers around each tubule think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
tubule_count = 25  # Number of tubules
layer_thickness = 0.06  # Thickness of the surrounding layer

# Function to create the tubules in a grid
def create_tubule_structure():
    # Build a cube and subtract tubules to form layers
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(tubule_count)]
    layer_objects = []
    
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean operation to cut inner tubule from cube
        cube_modifier = base_cube.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        # Create hollow layer around the tubule
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        layer_objects.append(inner_tubule)
    
    # Join all layer objects into one
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Combined_Layer_Shell"

# Execute the creation of the tubule structure
create_tubule_structure()
