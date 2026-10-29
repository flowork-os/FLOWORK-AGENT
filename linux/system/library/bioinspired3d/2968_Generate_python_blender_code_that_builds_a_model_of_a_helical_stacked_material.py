# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_that_builds_a_model_of_a_helical_stacked_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code that builds a model of a helical stacked material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
plies = 8  # Number of layers
rotation_angle = 10  # Rotation in degrees for each layer

def create_helical_layer(i):
    total_height = 2  # Complete height
    plate_size = 2  # Dimension of the square plate
    layer_thickness = total_height / plies  # Thickness of each layer

    # Determine the height for the current layer
    current_height = i * layer_thickness

    # Add a cube at the calculated height
    bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, current_height))
    layer = bpy.context.object

    # Scale to form a thin plate
    layer.scale[2] = layer_thickness / 2

    # Set the current layer as the active object
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate the layer around Z-axis
    bpy.ops.transform.rotate(value=math.radians(i * rotation_angle), orient_axis='Z')

# Generate the helical structure
for i in range(plies):
    create_helical_layer(i)
