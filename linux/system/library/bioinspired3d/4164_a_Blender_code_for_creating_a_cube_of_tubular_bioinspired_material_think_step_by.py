# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_creating_a_cube_of_tubular_bioinspired_material_think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for creating a cube of tubular bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 22

def create_tubular_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    cylinder_positions = [(start_offset + (i % grid_size) * spacing,
                           start_offset + (i // grid_size) * spacing)
                          for i in range(total_tubules)]
    
    for position in cylinder_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(position[0], position[1], 0))
        cylinder = bpy.context.object

        boolean_modifier = base_cube.modifiers.new(name=f"Cutout_{position[0]}_{position[1]}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = cylinder

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)

        bpy.data.objects.remove(cylinder, do_unlink=True)

create_tubular_structure()
