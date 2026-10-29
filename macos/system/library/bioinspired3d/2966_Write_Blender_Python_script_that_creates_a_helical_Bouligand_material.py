# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_that_creates_a_helical_Bouligand_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script that creates a helical Bouligand material.

import bpy
import math

# Remove all objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helix parameters
num_layers = 9  # Total number of layers
rotation_degrees = 20  # Rotation for each layer

def add_layer(index):
    height = 2  # Complete height of the structure
    size = 2  # Dimension of each square layer
    layer_height = height / num_layers  # Height of each layer

    z_position = index * layer_height
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position))
    layer = bpy.context.object
    layer.scale[2] = layer_height / 2

    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * rotation_degrees), orient_axis='Z')

# Construct the helical structure
for i in range(num_layers):
    add_layer(i)
