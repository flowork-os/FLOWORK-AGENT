# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_tubular_porous_structure_in_Blender_Python_script_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a tubular porous structure in Blender Python script Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

tubule_count = 25  # Defined number of tubules

def create_cylinders():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    coords = [(offset + (i % grid_size) * spacing,
                offset + (i // grid_size) * spacing)
               for i in range(tubule_count)]
    
    for x_pos, y_pos in coords:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
        cylinder = bpy.context.object

        bool_mod = cube_base.modifiers.new(name=f"Cutout_{x_pos}_{y_pos}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cylinder

        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(cylinder, do_unlink=True)

create_cylinders()
