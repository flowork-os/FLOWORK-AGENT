# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_create_a_tubular_bioinspired_material_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to create a tubular bioinspired material Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubules
count_of_tubules = 24  # Total number of tubules
ellipse_factor = 1.1  # Factor to stretch tubules
radius_of_tubules = 0.05  # Radius of the tubules

def setup_tubule_cube(count, ellipticity, radius):
    # Create a cube and arrange tubules within it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    for i in range(count):
        x = start_offset + (i % grid_size) * spacing
        y = start_offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        modifier = cube.modifiers.new(name=f"Boolean_{i}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the structure
setup_tubule_cube(count_of_tubules, ellipse_factor, radius_of_tubules)
