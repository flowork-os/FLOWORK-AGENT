# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_tubular_porous_bioinspired_material_in_a_Blender_code_think_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a tubular porous bioinspired material in a Blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 15  # Total number of tubular structures
elliptical_factor = 1.5  # Stretch factor for tubules
base_radius = 0.07  # Radius for the tubules

def build_tubular_structure(tubule_quantity, stretch_factor=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(tubule_quantity))
    gap = 2 / grid_dimension
    initial_offset = -1 + gap / 2
    positions = [(initial_offset + (i % grid_dimension) * gap, 
                  initial_offset + (i // grid_dimension) * gap) 
                 for i in range(tubule_quantity)]
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= stretch_factor
        bool_mod = main_cube.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

build_tubular_structure(num_tubules, elliptical_factor, base_radius)
