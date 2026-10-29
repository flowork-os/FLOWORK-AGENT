# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_script_that_generates_a_helical_structure_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender script that generates a helical structure think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
layers = 12  # Number of layers in the structure
rotation_step = 5  # Rotation angle in degrees for each layer

def create_helical_structure(layer_count, rotation):
    height = 2  # Total height of the structure
    plate_size = 2  # Size of each square plate
    thickness = height / layer_count  # Compute thickness

    for i in range(layer_count):
        z_position = i * thickness  # Calculate position in Z
        bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = thickness / 2  # Scale to thin plate

        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(i * rotation), orient_axis='Z')

create_helical_structure(layers, rotation_step)
