# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_building_a_cube_of_tubular_material_with_tubule_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for building a cube of tubular material with tubule layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubes = 25
layer_thickness = 0.03

def create_tube_grid():
    # Constructs a grid of tubular structures within a cube.
    # Steps:
    # 1. Add a cube.
    # 2. Calculate grid positions for tubules.
    # 3. Generate inner and outer tubules at each position.
    # 4. Subtract inner tubules from the cube using Boolean modifiers.
    # 5. Create the outer layer using Boolean modifiers.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubes))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_size) * spacing, 
                   offset + (i // grid_size) * spacing) 
                  for i in range(num_tubes)]
    
    tube_objects = []
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        
        # Boolean modifier to subtract inner tube from the cube
        modifier = base_cube.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        
        # Boolean modifier for creating the outer layer
        layer_modifier = inner_tube.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)
        
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        tube_objects.append(inner_tube)
    
    # Join all tubules into a single object
    if tube_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in tube_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = tube_objects[0]
        bpy.ops.object.join()
        merged_tubes = bpy.context.object
        merged_tubes.name = "Merged_Tubular_Structure"

# Execute the tube grid creation
create_tube_grid()
