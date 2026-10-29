# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_helical_material_using_code_in_Blender_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a helical material using code in Blender think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
ply_count = 7
rotation_angle_per_ply = 12

def create_layer(index):
    total_height = 2
    plate_size = 2
    thickness = total_height / ply_count

    # Calculate the vertical position for the layer
    vertical_position = index * thickness

    # Add a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, vertical_position))
    layer_object = bpy.context.object

    # Scale the cube to form a thin plate
    layer_object.scale[2] = thickness / 2

    # Set as active object
    bpy.context.view_layer.objects.active = layer_object
    layer_object.select_set(True)

    # Rotate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(index * rotation_angle_per_ply), orient_axis='Z')

# Construct the helical structure
for i in range(ply_count):
    create_layer(i)
