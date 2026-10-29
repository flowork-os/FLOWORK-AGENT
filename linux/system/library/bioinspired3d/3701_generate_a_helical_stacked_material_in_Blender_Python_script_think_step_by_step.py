# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_helical_stacked_material_in_Blender_Python_script_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a helical stacked material in Blender Python script think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical structure
layers_count = 10  # number of layers in the structure
angle_per_layer = 15  # rotation angle in degrees for each layer

def build_plate(layer_index):
    # Constructs a single plate for the helical structure.
    height_total = 2  # Complete height of the structure
    plate_dimension = 2  # Dimension of each square plate
    layer_thickness = height_total / layers_count  # Thickness of each layer

    # Determine vertical position of the layer
    vertical_position = layer_index * layer_thickness

    # Add a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(
        size=plate_dimension,
        location=(0, 0, vertical_position)
    )

    # Reference the newly created object
    plate_object = bpy.context.object

    # Scale the cube to form a thin plate
    plate_object.scale[2] = layer_thickness / 2

    # Set the plate as active and selected
    bpy.context.view_layer.objects.active = plate_object
    plate_object.select_set(True)

    # Rotate around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(layer_index * angle_per_layer),
        orient_axis='Z'
    )

    return plate_object

# Create the helical structure by iterating through the number of layers
for idx in range(layers_count):
    build_plate(idx)
