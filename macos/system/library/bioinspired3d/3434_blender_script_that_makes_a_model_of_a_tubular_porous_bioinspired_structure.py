# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_makes_a_model_of_a_tubular_porous_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that makes a model of a tubular porous bioinspired structure.

import bpy
import math

# Remove all existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the structure parameters
count_of_tubules = 12
ellipse_scale = 1.4
radius_of_tubules = 0.09

def setup_tubule_grid(count, ellipticity, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    start = -1 + spacing / 2
    positions = [(start + (i % grid_size) * spacing, start + (i // grid_size) * spacing) for i in range(count)]
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= ellipticity
        bool_modifier = base_cube.modifiers.new(name=f"Cut_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Build the tubular structure
setup_tubule_grid(count_of_tubules, ellipse_scale, radius_of_tubules)
