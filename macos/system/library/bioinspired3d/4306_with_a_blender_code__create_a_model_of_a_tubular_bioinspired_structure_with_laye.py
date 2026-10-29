# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_blender_code__create_a_model_of_a_tubular_bioinspired_structure_with_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a blender code, create a model of a tubular bioinspired structure with layers. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

number_of_tubules = 9  # Total number of tubules
layer_shell_thickness = 0.07  # Thickness of the surrounding shell

def build_tubule_structure():
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
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_shell_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        cube_modifier = base_object.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube_modifier.operation = 'DIFFERENCE'
        cube_modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = base_object
        bpy.ops.object.modifier_apply(modifier=cube_modifier.name)
        
        layer_modifier = inner_tubule.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        tubule_objects.append(inner_tubule)
    
    if tubule_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in tubule_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = tubule_objects[0]
        bpy.ops.object.join()
        final_tubule_shell = bpy.context.object
        final_tubule_shell.name = "Merged_Tubule_Shell"

build_tubule_structure()
