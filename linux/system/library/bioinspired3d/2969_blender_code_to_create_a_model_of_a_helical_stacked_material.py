# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_create_a_model_of_a_helical_stacked_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to create a model of a helical stacked material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical structure
number_of_layers = 6
angle_increment = 15

def generate_layer(index):
    height_total = 2
    plate_dimension = 2
    layer_thickness = height_total / number_of_layers

    # Calculate the height for the current layer
    height_position = index * layer_thickness

    # Create a cube at the specified height
    bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, height_position))
    created_layer = bpy.context.object

    # Scale the layer to make it thin
    created_layer.scale[2] = layer_thickness / 2

    # Set the layer as active
    bpy.context.view_layer.objects.active = created_layer
    created_layer.select_set(True)

    # Rotate the layer
    bpy.ops.transform.rotate(value=math.radians(index * angle_increment), orient_axis='Z')

# Build the helical structure
for idx in range(number_of_layers):
    generate_layer(idx)
