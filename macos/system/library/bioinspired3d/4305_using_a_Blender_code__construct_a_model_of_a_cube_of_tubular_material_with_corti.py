# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_code__construct_a_model_of_a_cube_of_tubular_material_with_corti" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender code, construct a model of a cube of tubular material with cortical layers. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure configuration
count_tubules = 20  # Number of tubules
thickness_layer = 0.06  # Thickness around each tubule

def create_structure(tubule_count, layer_thickness):
    # Create a cube as a base
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_size) * spacing, 
                  offset + (i // grid_size) * spacing) 
                 for i in range(tubule_count)]
    
    created_tubules = []
    
    for x, y in positions:
        # Create the inner cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_cylinder = bpy.context.object

        # Create the outer cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_cylinder = bpy.context.object
        
        # Boolean modifier to cut the inner cylinder from the cube
        cube_bool = cube_base.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube_bool.operation = 'DIFFERENCE'
        cube_bool.object = inner_cylinder
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=cube_bool.name)
        
        # Boolean modifier for the outer layer
        layer_bool = inner_cylinder.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_bool.operation = 'DIFFERENCE'
        layer_bool.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=layer_bool.name)

        # Delete the outer cylinder
        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        created_tubules.append(inner_cylinder)
    
    # Combine all inner tubules into a single object
    if created_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in created_tubules:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = created_tubules[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Final_Tubule_Shell"

# Create the tubular structure
create_structure(count_tubules, thickness_layer)
