# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_makes_a_model_of_a_tubular_bioinspired_material_think_step_b" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that makes a model of a tubular bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

count_of_tubules = 25
ellipse_factor = 2.0
cylinder_radius = 0.05

def create_tubule_grid(tubule_count, ellipticity_value, radius_value):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_length = math.ceil(math.sqrt(tubule_count))
    distance_between = 2 / grid_length
    offset_start = -1 + distance_between / 2

    positions = [(offset_start + (i % grid_length) * distance_between,
                  offset_start + (i // grid_length) * distance_between)
                 for i in range(tubule_count)]

    for x_pos, y_pos in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius_value, depth=3, location=(x_pos, y_pos, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= ellipticity_value

        bool_mod = main_cube.modifiers.new(name=f"Subtract_{x_pos}_{y_pos}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

create_tubule_grid(count_of_tubules, ellipse_factor, cylinder_radius)
