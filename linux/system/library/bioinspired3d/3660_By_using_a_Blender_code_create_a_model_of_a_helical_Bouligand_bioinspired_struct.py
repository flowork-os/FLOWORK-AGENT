# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code_create_a_model_of_a_helical_Bouligand_bioinspired_struct" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code create a model of a helical Bouligand bioinspired structure. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical structure
layers_count = 10  # total number of layers
angle_per_layer = 15  # degrees of rotation for each layer

def generate_layer(layer_index):
    height_of_structure = 2  # overall height
    square_size = 2  # dimensions of each square plate
    thickness_of_layer = height_of_structure / layers_count  # thickness of each layer

    z_position = layer_index * thickness_of_layer  # vertical position calculation

    bpy.ops.mesh.primitive_cube_add(size=square_size, location=(0, 0, z_position))
    layer = bpy.context.object  # reference to the created layer
    layer.scale[2] = thickness_of_layer / 2  # scale to create a thin layer

    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)  # select the layer

    bpy.ops.transform.rotate(value=math.radians(layer_index * angle_per_layer), orient_axis='Z')  # rotate the layer

    return layer

# Create the helical structure
for index in range(layers_count):
    generate_layer(index)
