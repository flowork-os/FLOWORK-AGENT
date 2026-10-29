# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_python_blender_code__construct_a_helical_twisted_ply_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with python blender code, construct a helical twisted ply bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
layers_count = 10  # Total number of layers
angle_per_layer = 5  # Degrees of rotation for each layer

def generate_layer(layer_index):
    height_of_structure = 2  # Overall height
    plate_dimension = 2  # Size of the square plate
    thickness_of_layer = height_of_structure / layers_count  # Layer thickness

    # Determine the vertical position for the layer
    vertical_position = layer_index * thickness_of_layer

    # Add a cube at the determined position
    bpy.ops.mesh.primitive_cube_add(
        size=plate_dimension,
        location=(0, 0, vertical_position)
    )

    current_plate = bpy.context.object

    # Scale the cube to make it a thin plate
    current_plate.scale[2] = thickness_of_layer / 2

    # Set the current plate as active and selected
    bpy.context.view_layer.objects.active = current_plate
    current_plate.select_set(True)

    # Rotate the plate around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(layer_index * angle_per_layer),
        orient_axis='Z'
    )

for index in range(layers_count):
    generate_layer(index)
