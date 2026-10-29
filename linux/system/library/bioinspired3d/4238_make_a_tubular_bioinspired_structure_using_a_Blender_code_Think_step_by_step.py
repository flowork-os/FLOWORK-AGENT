# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_tubular_bioinspired_structure_using_a_Blender_code_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a tubular bioinspired structure using a Blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

count_tubules = 25
ellipse_factor = 1.2
radius_tubule = 0.05

def create_tubular_structure(tubule_count, ellipticity, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2
    
    positions = []
    for i in range(tubule_count):
        x = start_offset + (i % grid_dim) * spacing
        y = start_offset + (i // grid_dim) * spacing
        positions.append((x, y))
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        
        modifier = main_cube.modifiers.new(name=f"Subtraction_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

create_tubular_structure(count_tubules, ellipse_factor, radius_tubule)
