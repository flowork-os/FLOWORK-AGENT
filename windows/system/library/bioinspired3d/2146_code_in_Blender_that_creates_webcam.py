# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_creates_webcam" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that creates webcam

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a class for the object creation
class ObjectCreator:
    @staticmethod
    def create_sphere(location):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=location)
        bpy.context.object.name = 'Camera'

    @staticmethod
    def create_cylinder(radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        bpy.context.object.name = name

# Create objects using the ObjectCreator class
ObjectCreator.create_sphere((0, 0, 0.5))
ObjectCreator.create_cylinder(0.1, 0.5, (0, 0, 0.25), 'Mount')
ObjectCreator.create_cylinder(0.3, 0.1, (0, 0, 0), 'Base')
