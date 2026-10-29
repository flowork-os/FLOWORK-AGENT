# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_helical_stacked_bioinspired_structure_with_randomness_in_rotation_using_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a helical stacked bioinspired structure with randomness in rotation using code in Blender think step by step.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

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

        rotation_value = i * rotation_step
        if add_noise:
            rotation_value += random.uniform(-max_noise, max_noise)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = current_layer
        current_layer.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

create_helical_layers(num_layers)
