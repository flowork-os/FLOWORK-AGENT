# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_blender_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of blender in blender python code

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to represent a 3D cylinder object
class Cylinder:
    def __init__(self, radius, height, position, name):
        self.radius = radius
        self.height = height
        self.position = position
        self.name = name
        self.create_cylinder()

    def create_cylinder(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=self.height, location=self.position)
        obj = bpy.context.object
        obj.name = self.name

# Create instances of the Cylinder class
Cylinder(1, 0.5, (0, 0, 0.25), 'Base')
Cylinder(0.8, 2, (0, 0, 1.5), 'Jar')
Cylinder(0.85, 0.2, (0, 0, 2.6), 'Lid')
