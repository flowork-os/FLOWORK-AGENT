# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_a_cube_of_tubular_material_in_blender_script_think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of a cube of tubular material in blender script think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_of_tubules = 9

def construct_tubule_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_of_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    for i in range(num_of_tubules):
        x = start_offset + (i % grid_size) * spacing
        y = start_offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        cylinder = bpy.context.object
        boolean_modifier = cube.modifiers.new(name=f"Subtract_{i}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = cylinder
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

construct_tubule_cube()
