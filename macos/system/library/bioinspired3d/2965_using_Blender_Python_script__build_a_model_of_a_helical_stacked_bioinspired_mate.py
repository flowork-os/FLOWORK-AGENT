# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_Python_script__build_a_model_of_a_helical_stacked_bioinspired_mate" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender Python script, build a model of a helical stacked bioinspired material.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical model
layers = 12  # Number of layers
angle_step = 5  # Angle for each layer in degrees

def create_helical_layer(i):
    total_height = 2  # Total height of the structure
    layer_size = 2  # Size of the square layer
    thickness = total_height / layers  # Thickness of each layer

    z_pos = i * thickness  # Layer's vertical position
    bpy.ops.mesh.primitive_cube_add(size=layer_size, location=(0, 0, z_pos))
    layer = bpy.context.object
    layer.scale[2] = thickness / 2  # Scale to create a thin layer

    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)  # Select the newly created layer
    bpy.ops.transform.rotate(value=math.radians(i * angle_step), orient_axis='Z')

# Build the helical structure
for layer_index in range(layers):
    create_helical_layer(layer_index)
