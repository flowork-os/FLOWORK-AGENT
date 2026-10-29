# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script__make_a_model_of_a_tubular_porous_bioinspired_material_wi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script, make a model of a tubular porous bioinspired material with layers around each tubule

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
tubule_count = 9
layer_thickness = 0.07

def create_structure():
    # Function to create a grid of tubules in a cubic form.
    # Steps:
    # 1. Add a cube.
    # 2. Determine positions for tubules in a grid.
    # 3. Create inner and outer tubules for each position.
    # 4. Subtract inner tubules from the cube using Boolean modifiers.
    # 5. Create a hollow layer using Boolean modifiers.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    positions = [(start_offset + (i % grid_size) * spacing, 
                   start_offset + (i // grid_size) * spacing) 
                  for i in range(tubule_count)]
    
    layer_objects = []
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        
        # Boolean modifier to subtract inner tubule from the cube
        modifier = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = inner_tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        
        # Create the hollow shell around the inner tubule
        shell_modifier = inner_tubule.modifiers.new(name=f"Shell_{x}_{y}", type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)
        
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        layer_objects.append(inner_tubule)
    
    # Merge all tubules into a single object
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Final_Tubular_Structure"

# Create the tubular structure
create_structure()
