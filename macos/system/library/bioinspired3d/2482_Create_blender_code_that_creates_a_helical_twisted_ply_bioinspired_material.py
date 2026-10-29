# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_blender_code_that_creates_a_helical_twisted_ply_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create blender code that creates a helical twisted ply bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
num_layers = 12  # Total layers in the helical design
angle_step = 20  # Degrees of rotation per layer

def create_helical_structure():
    total_height = 2
    plate_side = 2
    thickness_per_layer = total_height / num_layers

    for i in range(num_layers):
        z_position = i * thickness_per_layer
        bpy.ops.mesh.primitive_cube_add(size=plate_side, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = thickness_per_layer / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * angle_step), orient_axis='Z')

# Create the helical structure
create_helical_structure()
