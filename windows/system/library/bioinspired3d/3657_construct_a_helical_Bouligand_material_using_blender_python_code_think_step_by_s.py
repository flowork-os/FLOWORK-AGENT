# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_helical_Bouligand_material_using_blender_python_code_think_step_by_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a helical Bouligand material using blender python code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers_count = 10  # number of layers in the structure
angle_per_layer = 15  # rotation angle in degrees for each layer

# Function to generate a single layer
def generate_layer(layer_index):
    height_total = 2  # Overall height of the structure
    plate_dimension = 2  # Length of each square plate
    layer_thickness = height_total / layers_count  # Thickness of each layer

    # Determine the vertical position for the layer
    z_position = layer_index * layer_thickness

    # Add a cube at the specified position
    bpy.ops.mesh.primitive_cube_add(
        size=plate_dimension,
        location=(0, 0, z_position)
    )

    # Reference to the newly created object
    layer = bpy.context.object

    # Scale the cube to form a thin layer
    layer.scale[2] = layer_thickness / 2

    # Set the layer as the active object
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around the Z-axis
    bpy.ops.transform.rotate(
        value=math.radians(layer_index * angle_per_layer),
        orient_axis='Z'
    )

    return layer

# Create the helical structure
for index in range(layers_count):
    generate_layer(index)
