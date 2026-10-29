# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_helical_twisted_ply_bioinspired_material_in_a_blender_code_think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a helical twisted ply bioinspired material in a blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical parameters
plies_count = 10
rotation_step = 5

def add_helix_layer(layer_index):
    # Create a single layer for the helix
    total_height = 2
    plate_dimension = 2
    layer_depth = total_height / plies_count

    # Determine the Z position for this layer
    z_pos = layer_index * layer_depth

    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=plate_dimension, location=(0, 0, z_pos))
    current_layer = bpy.context.object

    # Scale the layer
    current_layer.scale[2] = layer_depth / 2

    # Rotate the layer
    bpy.ops.transform.rotate(value=math.radians(layer_index * rotation_step), orient_axis='Z')

# Loop to create all layers
for idx in range(plies_count):
    add_helix_layer(idx)
