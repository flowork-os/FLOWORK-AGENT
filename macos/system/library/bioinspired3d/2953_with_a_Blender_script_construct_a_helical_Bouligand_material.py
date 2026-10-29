# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_script_construct_a_helical_Bouligand_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender script construct a helical Bouligand material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the helical structure
num_layers = 9  # Number of layers in the structure
angle_step = 14  # Rotation angle for each layer

def build_helical_model():
    total_height = 2
    plate_dimension = 2
    layer_thickness = total_height / num_layers

    for layer_index in range(num_layers):
        z_coord = layer_index * layer_thickness
        bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, z_coord))
        current_plate = bpy.context.object
        current_plate.scale[2] = layer_thickness / 2
        bpy.context.view_layer.objects.active = current_plate
        current_plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(layer_index * angle_step), orient_axis='Z')

# Execute model building
build_helical_model()
