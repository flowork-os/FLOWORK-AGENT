# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_create_a_helical_stacked_bioinspired_material__Think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script create a helical stacked bioinspired material. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical model
layers = 15
angle_increment = 3

def make_plate(index):
    # Function to create a plate in the helical structure
    structure_height = 2
    plate_length = 2
    layer_thickness = structure_height / layers
    z_coord = index * layer_thickness

    bpy.ops.mesh.primitive_cube_add(size=plate_length, location=(0, 0, z_coord))
    plate = bpy.context.object
    plate.scale[2] = layer_thickness / 2
    bpy.context.view_layer.objects.active = plate
    plate.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(index * angle_increment), orient_axis='Z')

# Generate helical plates
for i in range(layers):
    make_plate(i)
