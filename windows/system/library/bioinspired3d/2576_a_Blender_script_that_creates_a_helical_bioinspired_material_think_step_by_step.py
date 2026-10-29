# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_creates_a_helical_bioinspired_material_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that creates a helical bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure setup
layer_count = 15  # number of layers
angle_increment = 20  # degrees of rotation per layer

def add_layer(index):
    total_height = 2
    cube_size = 2
    layer_height = total_height / layer_count

    z_pos = index * layer_height
    bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(0, 0, z_pos))
    layer = bpy.context.object
    layer.scale[2] = layer_height / 2

    bpy.context.view_layer.objects.active = layer
    layer.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * angle_increment), orient_axis='Z')

# Iterate to create the helical structure
for idx in range(layer_count):
    add_layer(idx)
