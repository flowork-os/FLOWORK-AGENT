# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_code_make_a_helical_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender code make a helical structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical design
layers = 8  # Total number of layers
rotation_step = 20  # Degrees of rotation for each layer

for layer_index in range(layers):
    height = 2  # Total height of the structure
    plate_size = 2  # Dimension of the plate
    thickness = height / layers  # Layer thickness
    z_position = layer_index * thickness

    bpy.ops.mesh.primitive_cube_add(size=plate_size, location=(0, 0, z_position))
    plate = bpy.context.object
    plate.scale[2] = thickness / 2
    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(layer_index * rotation_step), orient_axis='Z')
