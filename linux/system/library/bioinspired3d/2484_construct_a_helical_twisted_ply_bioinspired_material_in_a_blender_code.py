# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_twisted_ply_bioinspired_material_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical twisted ply bioinspired material in a blender code

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for helical structure
total_layers = 8
rotation_angle = 10

def add_helical_plate(index):
    # This function adds a single plate at the specified index.
    full_height = 2
    plate_dimension = 2
    thickness_per_plate = full_height / total_layers

    # Determine the height for the current plate
    current_height = index * thickness_per_plate

    # Create a cube at the calculated height
    bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, current_height))

    new_plate = bpy.context.object

    # Scale the plate to make it thin
    new_plate.scale[2] = thickness_per_plate / 2

    # Activate the new plate for transformation
    bpy.context.view_layer.objects.active = new_plate
    new_plate.select_set(True)

    # Rotate the plate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(index * rotation_angle), orient_axis='Z')

for i in range(total_layers):
    add_helical_plate(i)
