# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_makes_a_model_of_a_helical_bioinspired_material_with_noise" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that makes a model of a helical bioinspired material with noise.

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical layers
layer_total = 9  # Number of layers
rotation_increment = 12  # Rotation increment per layer
noise_enabled = True  # Use noise for rotation
max_rotation_noise = 8  # Max noise amount

def create_helical_structure(total_layers, rotation_step, noise, max_noise):
    for i in range(total_layers):
        height = 2
        layer_size = 2
        layer_thickness = height / total_layers
        z_position = i * layer_thickness

        # Create cube
        bpy.ops.mesh.primitive_cube_add(size=layer_size, location=(0, 0, z_position))
        layer_object = bpy.context.object
        layer_object.scale[2] = layer_thickness / 2

        # Calculate rotation
        rotation_value = i * rotation_step
        if noise:
            rotation_value += random.uniform(-max_noise, max_noise)

        # Select the current layer
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = layer_object
        layer_object.select_set(True)

        # Rotate the layer
        bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

# Execute the structure creation
create_helical_structure(layer_total, rotation_increment, noise_enabled, max_rotation_noise)
