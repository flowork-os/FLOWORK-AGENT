# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_Blender_code_that_creates_a_model_of_a_helical_stacked_bioinspired_struct" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create Blender code that creates a model of a helical stacked bioinspired structure

import bpy
import math

# Clear the existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical parameters
layer_total = 9  # Number of layers
rotation_step = 20  # Degree of rotation for each layer

def create_helical_layers(total_layers, rotation_step):
    height = 2
    size = 2
    layer_thickness = height / total_layers

    # Generate layers
    for i in range(total_layers):
        z_pos = i * layer_thickness
        bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_pos))
        layer = bpy.context.object
        layer.scale[2] = layer_thickness / 2

        # Rotate the layer
        bpy.context.view_layer.objects.active = layer
        layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation_step), orient_axis='Z')

# Create the helical structure
create_helical_layers(layer_total, rotation_step)
