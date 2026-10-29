# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_makes_a_model_of_a_tubular_porous_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that makes a model of a tubular porous bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular arrangement
number_of_tubules = 16  # Total number of tubules
stretch_factor = 1.5  # Factor to stretch tubules into ellipses
base_radius = 0.07  # Base radius of the tubules

# Function to create a cube with tubules

def construct_tubule_cube(tubule_count, ellipticity, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2

    positions = [(initial_offset + (i % grid_dimension) * spacing,
                  initial_offset + (i // grid_dimension) * spacing)
                 for i in range(tubule_count)]

    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= ellipticity

        bool_modifier = main_cube.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

construct_tubule_cube(number_of_tubules, stretch_factor, base_radius)
