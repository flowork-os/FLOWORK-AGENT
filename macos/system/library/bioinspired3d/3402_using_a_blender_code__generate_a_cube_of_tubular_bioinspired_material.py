# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_blender_code__generate_a_cube_of_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a blender code, generate a cube of tubular bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular arrangement
count_tubules = 25  # Number of tubules
ellipse_factor = 1.2  # Factor for elongating tubules
radius_tubule = 0.05  # Radius for each tubule


def create_tubule_grid(total_tubules, ellipse=1.0, radius=0.1):
    # Creates a grid of tubules in a cube.
    # Process:
    # 1. Add a cube.
    # 2. Arrange tubules in a grid.
    # 3. Apply Boolean modifiers to subtract tubules.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object

    dimension = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / dimension
    offset = -1 + spacing / 2

    positions = [(offset + (i % dimension) * spacing,
                  offset + (i // dimension) * spacing)
                 for i in range(total_tubules)]

    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipse

        mod = cube.modifiers.new(name=f"Subtraction_{x}_{y}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = tubule

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=mod.name)

        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the tubular structure
create_tubule_grid(count_tubules, ellipse_factor, radius_tubule)
