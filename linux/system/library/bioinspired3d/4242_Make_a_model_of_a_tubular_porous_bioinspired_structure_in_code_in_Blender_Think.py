# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_tubular_porous_bioinspired_structure_in_code_in_Blender_Think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a tubular porous bioinspired structure in code in Blender Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular formation
number_of_tubules = 16  # Total number of individual tubules
stretch_factor = 1.5  # Factor to stretch tubules into ellipses
base_radius = 0.07  # Base radius of the tubules

# Function to create a grid of tubules in a cube
def generate_tubule_structure(count, stretch=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(count))
    spacing_distance = 2 / grid_dimension
    initial_offset = -1 + spacing_distance / 2

    positions = [(initial_offset + (i % grid_dimension) * spacing_distance,
                  initial_offset + (i // grid_dimension) * spacing_distance)
                 for i in range(count)]

    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        tubule_object = bpy.context.object
        tubule_object.scale[0] *= stretch

        bool_modifier = cube_object.modifiers.new(name=f"Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_object

        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule_object, do_unlink=True)

# Create the tubular structure
generate_tubule_structure(number_of_tubules, stretch_factor, base_radius)
