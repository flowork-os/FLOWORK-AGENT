# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_makes_a_helical_Bouligand_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that makes a helical Bouligand material.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical construction
number_of_layers = 6  # Layers in the structure
rotation_step = 18  # Degrees of rotation per layer

for layer_index in range(number_of_layers):
    # Calculate parameters for each layer
    height_of_structure = 2
    plate_size = 2
    thickness_of_layer = height_of_structure / number_of_layers
    z_position = layer_index * thickness_of_layer

    # Create a cube and adjust its size
    bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = thickness_of_layer / 2

    # Rotate the layer
    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(layer_index * rotation_step), orient_axis='Z')
