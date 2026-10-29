# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_tubular_bioinspired_material_using_Blender_Python_script_Think_step_b" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a tubular bioinspired material using Blender Python script Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_protrusions = 16  # Set the total count of protrusions

def generate_protrusions():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(num_protrusions))
    cylinder_spacing = 2 / grid_dimension
    initial_offset = -1 + cylinder_spacing / 2
    
    cylinder_positions = [(initial_offset + (i % grid_dimension) * cylinder_spacing,
                           initial_offset + (i // grid_dimension) * cylinder_spacing)
                          for i in range(num_protrusions)]
    
    for pos_x, pos_y in cylinder_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        cylinder = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = cylinder

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(cylinder, do_unlink=True)

generate_protrusions()
