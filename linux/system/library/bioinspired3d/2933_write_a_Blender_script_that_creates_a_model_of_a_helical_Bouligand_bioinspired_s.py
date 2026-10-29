# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_script_that_creates_a_model_of_a_helical_Bouligand_bioinspired_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender script that creates a model of a helical Bouligand bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure configuration
layers = 15  # Number of layers in the helical structure
angle_per_layer = 3  # Rotation angle for each layer in degrees

def create_layer(index):
    total_height = 2
    plate_size = 2
    layer_height = total_height / layers
    z_position = index * layer_height

    bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
    plate = bpy.context.object
    plate.scale[2] = layer_height / 2
    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * angle_per_layer), orient_axis='Z')

for i in range(layers):
    create_layer(i)
