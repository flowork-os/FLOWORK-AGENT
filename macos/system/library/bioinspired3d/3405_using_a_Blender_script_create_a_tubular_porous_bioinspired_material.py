# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script_create_a_tubular_porous_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script create a tubular porous bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
num_tubules = 10
ellipticity_value = 1.4
radius_value = 0.09


def form_tubule_cube(tubule_count, ellipticity=1.0, radius=0.1):
    # Constructs a cube filled with tubules arranged in a grid.
    # Steps:
    # 1. Create a cube.
    # 2. Generate tubules in a grid.
    # 3. Subtract tubules using Boolean modifiers.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object

    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset_start = -1 + spacing / 2

    positions = [(offset_start + (i % grid_size) * spacing,
                  offset_start + (i // grid_size) * spacing)
                 for i in range(tubule_count)]

    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule_obj = bpy.context.object
        tubule_obj.scale[0] *= ellipticity

        bool_mod = cube_obj.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule_obj

        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(tubule_obj, do_unlink=True)

# Generate the tubular formation
form_tubule_cube(num_tubules, ellipticity_value, radius_value)
