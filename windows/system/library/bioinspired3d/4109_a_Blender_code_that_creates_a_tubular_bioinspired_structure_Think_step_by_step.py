# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_creates_a_tubular_bioinspired_structure_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that creates a tubular bioinspired structure Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cylinders = 12  # Total cylinders in the grid

def build_structure():
    """Builds a cube with cylinders removed from it."""
    
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(num_cylinders))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    positions = [(start_offset + (i % grid_size) * spacing,
                   start_offset + (i // grid_size) * spacing)
                  for i in range(num_cylinders)]
    
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        cylinder = bpy.context.object
        bool_modifier = base.modifiers.new(name=f"CutCylinder_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = cylinder
        bpy.context.view_layer.objects.active = base
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

build_structure()
