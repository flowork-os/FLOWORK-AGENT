# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_script__create_a_model_of_a_helical_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender script, create a model of a helical bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical structure parameters
ply_count = 7  # Number of plies in the helical structure
rotation_angle = 10  # Angle for each ply in degrees

class HelicalPlate:
    def __init__(self, index):
        self.index = index
        self.height = 2
        self.size = 2
        self.thickness = self.height / ply_count

    def create(self):
        z_position = self.index * self.thickness
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=(0, 0, z_position))
        plate = bpy.context.object
        plate.scale[2] = self.thickness / 2
        bpy.context.view_layer.objects.active = plate
        plate.select_set(True)
        bpy.ops.transform.rotate(value=math.radians(self.index * rotation_angle), orient_axis='Z')

# Generating the helical plates
for i in range(ply_count):
    HelicalPlate(i).create()
