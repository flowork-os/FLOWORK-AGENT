# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_making_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for making a tubular bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular arrangement
num_tubules = 16  # Total number of tubules
stretch_factor = 1.5  # Factor to stretch tubules into ellipses
base_radius = 0.08  # Radius of the tubules


def build_tubule_structure(tubule_count, ellipticity=1.0, radius=0.1):
    # Constructs a cube and subtracts tubules from it.
    # 1. Create a cube.
    # 2. Place tubules in a grid layout.
    # 3. Use Boolean modifiers to cut out the tubules.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(tubule_count)]
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        boolean_mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
build_tubule_structure(num_tubules, stretch_factor, base_radius)
