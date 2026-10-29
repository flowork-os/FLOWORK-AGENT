# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_constructs_a_model_of_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that constructs a model of drum.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to represent a drum
class Drum:
    def __init__(self, radius_body, depth_body, radius_head, depth_head):
        self.body = self.create_part(radius_body, depth_body, (0, 0, 0.75), 'Drum Body')
        self.head = self.create_part(radius_head, depth_head, (0, 0, 1.55), 'Drumhead')

    @staticmethod
    def create_part(radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        obj = bpy.context.object
        obj.name = name
        return obj

# Instantiate the drum
my_drum = Drum(1, 1.5, 1.05, 0.1)
