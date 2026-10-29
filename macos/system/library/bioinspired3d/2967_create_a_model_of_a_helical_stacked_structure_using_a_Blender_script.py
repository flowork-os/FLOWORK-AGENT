# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_helical_stacked_structure_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a helical stacked structure using a Blender script

import bpy
import math

# Clear the scene of all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
total_layers = 15  # Number of layers
layer_rotation = 3  # Rotation in degrees for each layer

def build_helical_layers():
    total_height = 2  # Overall height of the structure
    square_size = 2  # Size of each square layer
    thickness_per_layer = total_height / total_layers  # Thickness of each layer

    for i in range(total_layers):
        z_position = i * thickness_per_layer
        bpy.ops.mesh.primitive_cube_add(size=square_size, location=(0, 0, z_position))
        current_layer = bpy.context.object
        current_layer.scale[2] = thickness_per_layer / 2

        bpy.context.view_layer.objects.active = current_layer
        current_layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * layer_rotation), orient_axis='Z')

# Execute the layer building function
build_helical_layers()
