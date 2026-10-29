# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code_generate_a_model_of_a_helical_twisted_ply_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code generate a model of a helical twisted ply material with rotational noise.

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical parameters
num_layers = 12  # Total layers
rotation_step = 5  # Degrees per layer
add_noise = True  # Enable noise
max_noise = 7  # Max noise in degrees

def create_helical_layers(total_layers):
    height = 2
    cube_size = 2
    layer_height = height / total_layers

    for i in range(total_layers):
        z_offset = i * layer_height
        bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_offset))
        current_layer = bpy.context.object
        current_layer.scale[2] = layer_height / 2

        # Determine rotation with noise
        rotation_value = i * rotation_step
        if add_noise:
            rotation_value += random.uniform(-max_noise, max_noise)

        # Rotate the layer
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = current_layer
        current_layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

# Execute the layer creation
create_helical_layers(num_layers)
