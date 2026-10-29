# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_Bouligand_structure_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical Bouligand structure using a Blender script

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layer_count = 14
angle_per_layer = 8

def create_layer(index):
    height = 2
    plate_size = 2
    thickness = height / layer_count

    # Calculate Z position
    z_position = index * thickness

    # Create a cube at the specified location
    bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
    layer = bpy.context.object

    # Scale down to form a plate
    layer.scale[2] = thickness / 2

    # Rotate around Z-axis
    bpy.ops.transform.rotate(value=math.radians(index * angle_per_layer), orient_axis='Z')

# Generate the helical structure
for i in range(layer_count):
    create_layer(i)
