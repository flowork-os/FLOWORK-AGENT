# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_tubular_porous_structure_in_Blender_code_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a tubular porous structure in Blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 20

def create_geometry():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_shape = bpy.context.object

    grid_dim = math.ceil(math.sqrt(total_tubules))
    distance = 2 / grid_dim
    offset = -1 + distance / 2

    for index in range(total_tubules):
        x_pos = offset + (index % grid_dim) * distance
        y_pos = offset + (index // grid_dim) * distance
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
        current_tubule = bpy.context.object

        modifier = base_shape.modifiers.new(name=f"Cut_{index}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = current_tubule

        bpy.context.view_layer.objects.active = base_shape
        bpy.ops.object.modifier_apply(modifier=modifier.name)

        bpy.data.objects.remove(current_tubule, do_unlink=True)

create_geometry()
