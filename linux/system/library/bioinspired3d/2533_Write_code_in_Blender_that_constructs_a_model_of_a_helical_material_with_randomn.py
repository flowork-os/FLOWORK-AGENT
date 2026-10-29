# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_that_constructs_a_model_of_a_helical_material_with_randomn" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender that constructs a model of a helical material with randomness in rotation

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
num_layers = 12
rotation_step = 5
noise_toggle = True
noise_deviation = 6

def create_helical_layers(num_layers):
    for i in range(num_layers):
        create_layer(i)

def create_layer(index):
    height_total = 2
    cube_size = 2
    layer_thickness = height_total / num_layers
    z_position = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = layer_thickness / 2

    rotation_value = index * rotation_step
    if noise_toggle:
        rotation_value += random.uniform(-noise_deviation, noise_deviation)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis='Z')

# Execute layer creation
create_helical_layers(num_layers)
