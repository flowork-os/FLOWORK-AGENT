# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_helical_Bouligand_structure_with_randomness_in_rotation_using_a_Blend" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a helical Bouligand structure with randomness in rotation using a Blender code

import bpy
import math
import random

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the helical structure parameters
num_layers = 12
angle_increment = 5
is_noise_enabled = True
noise_variation = 6

def create_helical_structure(num_layers):
    for i in range(num_layers):
        create_single_layer(i)

def create_single_layer(index):
    height = 2
    cube_size = 2
    layer_thickness = height / num_layers
    z_offset = index * layer_thickness

    # Create cube mesh
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_offset))
    layer = bpy.context.object
    layer.scale[2] = layer_thickness / 2

    # Calculate rotation
    rotation_angle = index * angle_increment
    if is_noise_enabled:
        rotation_angle += random.uniform(-noise_variation, noise_variation)

    # Deselect all and set current layer for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    # Rotate layer
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

# Execute creation of the helical structure
create_helical_structure(num_layers)
