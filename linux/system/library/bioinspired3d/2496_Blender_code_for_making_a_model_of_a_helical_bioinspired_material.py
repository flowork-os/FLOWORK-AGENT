# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_making_a_model_of_a_helical_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for making a model of a helical bioinspired material.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
layer_count = 15  # Number of layers in the structure
rotation_angle = 3  # Rotation angle for each layer

# Function to create a helical structure
def helical_structure(layer_count, rotation_angle):
    total_height = 2
    plate_size = 2
    layer_height = total_height / layer_count

    for i in range(layer_count):
        z_position = i * layer_height
        bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = layer_height / 2

        # Rotate the plate
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_angle), orient_axis='Z')

# Execute the creation of the helical structure
helical_structure(layer_count, rotation_angle)
