# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_python_blender_code_generate_a_model_of_a_tubular_structure_with_layers__th" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With python blender code generate a model of a tubular structure with layers. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
tubule_count = 12  # Number of tubules
layer_thickness = 0.05  # Thickness of the surrounding layer

# Functional approach to create tubules
def generate_tubules(count, thickness):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(count)]
    layer_objects = []
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Subtract inner tubule from cube
        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Create hollow layer around the tubule
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        layer_objects.append(inner_tubule)
    
    # Join all layers into a single object
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Combined_Layer_Shell"

# Execute the function to create the tubular structure
generate_tubules(tubule_count, layer_thickness)
