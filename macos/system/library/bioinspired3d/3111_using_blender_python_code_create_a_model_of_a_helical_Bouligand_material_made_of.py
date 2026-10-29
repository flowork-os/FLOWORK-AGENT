# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_python_code_create_a_model_of_a_helical_Bouligand_material_made_of" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender python code create a model of a helical Bouligand material made of cylindrical fibers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber structure
layer_count = 15  # Total layers in the structure
rotation_step = 3  # Rotation angle in degrees for each layer
fiber_shape = 'cylinder'  # Shape of fibers

# Dimensions of the structure
structure_height = 2.0  # Total height of the structure
plate_length = 2.0  # Width and length of each plate
layer_height = structure_height / layer_count  # Height of each layer

def create_fiber_object(x, y, z):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=layer_height / 2,
        depth=plate_length,
        location=(x, y, z),
        rotation=(0, math.radians(90), 0)
    )

for i in range(layer_count):
    z_position = i * layer_height
    angle = i * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_layer = bpy.context.object

    fiber_num = max(1, int(plate_length / (layer_height / 2)))
    starting_y = -plate_length / 2 + (layer_height / 2) + (plate_length - fiber_num * (layer_height / 2)) / 2

    for j in range(fiber_num):
        current_y = starting_y + j * (layer_height / 2)
        create_fiber_object(0, current_y, z_position)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_layer
    empty_layer.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(angle),
        orient_axis='Z'
    )
