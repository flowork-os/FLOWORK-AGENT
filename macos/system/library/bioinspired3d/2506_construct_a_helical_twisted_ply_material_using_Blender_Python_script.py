# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_twisted_ply_material_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical twisted ply material using Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Rotation angle for each layer

def add_layer(layer_index):
    height_of_structure = 2  # Overall height of the structure
    plate_dimension = 2  # Dimensions of each square plate
    layer_thickness = height_of_structure / layers_count  # Thickness of each layer

    # Determine the vertical position
    vertical_position = layer_index * layer_thickness

    # Create a cube at the computed position
    bpy.ops.mesh.primitive_cube_add(
        size=plate_dimension,
        location=(0, 0, vertical_position)
    )

    current_layer = bpy.context.object

    # Scale the cube to form a thin plate
    current_layer.scale[2] = layer_thickness / 2

    # Set the current layer as active and selected
    bpy.context.view_layer.objects.active = current_layer
    current_layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(layer_index * angle_per_layer),
        orient_axis='Z'
    )

    return current_layer

# Create the helical structure
for index in range(layers_count):
    add_layer(index)
