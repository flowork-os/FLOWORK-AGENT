# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_making_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for making bird feeder.

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a class to create 3D objects
class ObjectCreator:
    @staticmethod
    def create_cylinder(radius, height, position, obj_name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
        obj = bpy.context.object
        obj.name = obj_name
        return obj

    @staticmethod
    def create_cone(radius, height, position, obj_name):
        bpy.ops.mesh.primitive_cone_add(radius1=radius, depth=height, location=position)
        obj = bpy.context.object
        obj.name = obj_name
        return obj

# Instantiate the ObjectCreator and create the shapes
creator = ObjectCreator()
main_part = creator.create_cylinder(0.5, 1.0, (0, 0, 0.5), 'Main Cylinder')
roof_part = creator.create_cone(0.6, 0.3, (0, 0, 1.15), 'Cone Roof')
perch_part = creator.create_cylinder(0.05, 0.8, (0.5, 0, 0.3), 'Side Perch')
perch_part.rotation_euler[1] = math.pi / 2
