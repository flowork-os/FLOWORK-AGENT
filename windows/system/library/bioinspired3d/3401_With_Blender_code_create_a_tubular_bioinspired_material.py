# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_code_create_a_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender code create a tubular bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular formation
number_of_tubules = 16  # Total count of tubules
stretch_factor = 1.5  # Ellipticity factor for tubules
base_radius = 0.07  # Radius of the tubules


def build_tubule_structure(tubule_count, ellipticity=1.0, radius=0.1):
    # Constructs a grid of tubules within a cube.
    # Steps:
    # 1. Create a cube.
    # 2. Position tubules in a grid.
    # 3. Subtract tubules using Boolean modifiers.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object

    grid_dimension = math.ceil(math.sqrt(tubule_count))
    spacing_between_tubules = 2 / grid_dimension
    initial_offset = -1 + spacing_between_tubules / 2

    tubule_positions = [(initial_offset + (i % grid_dimension) * spacing_between_tubules,
                         initial_offset + (i // grid_dimension) * spacing_between_tubules)
                        for i in range(tubule_count)]

    for position in tubule_positions:
        x, y = position
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule_object = bpy.context.object
        tubule_object.scale[0] *= ellipticity

        boolean_modifier = cube_object.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule_object

        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)

        bpy.data.objects.remove(tubule_object, do_unlink=True)

# Execute the tubule creation
build_tubule_structure(number_of_tubules, stretch_factor, base_radius)
