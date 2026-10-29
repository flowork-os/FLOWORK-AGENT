# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_code__generate_a_model_of_a_helical_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender code, generate a model of a helical bioinspired material.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
plys = 7  # Number of plies
rotation_angle = 18  # Angle of rotation per ply

# Function to create a ply
def create_ply(index):
    height_total = 2  # Total height of the structure
    ply_size = 2  # Size of each ply
    ply_thickness = height_total / plys  # Thickness of each ply

    # Calculate the height for this ply
    z_position = index * ply_thickness

    # Add a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=ply_size, location=(0, 0, z_position))
    ply_object = bpy.context.object

    # Scale the ply to make it thin
    ply_object.scale[2] = ply_thickness / 2

    # Select the ply object
    bpy.context.view_layer.objects.active = ply_object
    ply_object.select_set(True)

    # Rotate around the Z-axis
    bpy.ops.transform.rotate(value=math.radians(index * rotation_angle), orient_axis='Z')

# Generate the helical structure
for i in range(plys):
    create_ply(i)
