# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_builds_a_model_of_a_cube_of_tubular_material__Think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that builds a model of a cube of tubular material. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tube_count = 20

def create_structure(tube_count):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(tube_count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    positions = []
    for i in range(tube_count):
        x = offset + (i % grid_dim) * spacing
        y = offset + (i // grid_dim) * spacing
        positions.append((x, y))
    
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        
        bool_modifier = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tube, do_unlink=True)

create_structure(tube_count)
