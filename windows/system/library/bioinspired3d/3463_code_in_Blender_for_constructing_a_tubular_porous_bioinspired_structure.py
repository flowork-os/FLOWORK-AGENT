# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_constructing_a_tubular_porous_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for constructing a tubular porous bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the tubular model
count_tubules = 20  # Total number of tubules
elliptical_ratio = 1.8  # Stretching factor for tubules
radius_tubule = 0.07  # Radius of the tubules

def build_tubule_structure(count_tubules, elliptical_ratio=1.0, radius_tubule=0.1):
    # Start by creating the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(count_tubules))
    spacing_distance = 2 / grid_dimension
    initial_offset = -1 + spacing_distance / 2
    for i in range(count_tubules):
        pos_x = initial_offset + (i % grid_dimension) * spacing_distance
        pos_y = initial_offset + (i // grid_dimension) * spacing_distance
        bpy.ops.mesh.primitive_cylinder_add(radius=radius_tubule, depth=3, location=(pos_x, pos_y, 0))
        new_tubule = bpy.context.object
        new_tubule.scale[0] *= elliptical_ratio
        boolean_modifier = base_cube.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = new_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(new_tubule, do_unlink=True)

build_tubule_structure(count_tubules, elliptical_ratio, radius_tubule)
