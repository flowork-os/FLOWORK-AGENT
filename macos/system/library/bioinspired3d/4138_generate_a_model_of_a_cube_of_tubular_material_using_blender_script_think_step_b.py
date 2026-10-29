# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_cube_of_tubular_material_using_blender_script_think_step_b" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a cube of tubular material using blender script think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 20

def generate_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_count = math.ceil(math.sqrt(total_tubules))
    distance = 2 / grid_count
    offset = -1 + distance / 2
    
    positions = []
    for i in range(total_tubules):
        x = offset + (i % grid_count) * distance
        y = offset + (i // grid_count) * distance
        positions.append((x, y))
    
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        boolean_modifier = base_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tube, do_unlink=True)

generate_tubules()
