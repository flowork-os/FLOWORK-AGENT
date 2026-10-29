# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_building_a_model_of_a_helical_twisted_ply_bioinspired_materia" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for building a model of a helical twisted ply bioinspired material. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
num_layers = 6
rotation_angle = 20

# Function to create a helical layer
def create_helical_layer(index):
    height_of_structure = 2
    plate_side = 2
    layer_thickness = height_of_structure / num_layers

    z_position = index * layer_thickness

    # Add a cube at the calculated position
    bpy.ops.mesh.primitive_cube_add(size=plate_side, location=(0, 0, z_position))
    layer = bpy.context.object

    # Scale the layer to make it thin
    layer.scale[2] = layer_thickness / 2

    # Rotate the layer around Z-axis
    bpy.ops.transform.rotate(value=math.radians(index * rotation_angle), orient_axis='Z')

# Generate the helical layers
for i in range(num_layers):
    create_helical_layer(i)
