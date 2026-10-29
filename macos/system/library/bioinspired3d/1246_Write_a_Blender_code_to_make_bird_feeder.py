# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_code_to_make_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender code to make bird feeder

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to build the 3D model components
class ModelBuilder:
    def __init__(self):
        self.objects = []

    def add_cylinder(self, radius, depth, location, rotation=(0, 0, 0), name='Cylinder'):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
        obj = bpy.context.object
        obj.name = name
        self.objects.append(obj)

    def add_cone(self, radius, depth, location, name='Cone'):
        bpy.ops.mesh.primitive_cone_add(radius1=radius, depth=depth, location=location)
        obj = bpy.context.object
        obj.name = name
        self.objects.append(obj)

    def add_torus(self, major_radius, minor_radius, location, rotation=(0, 0, 0), name='Torus'):
        bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, location=location, rotation=rotation)
        obj = bpy.context.object
        obj.name = name
        self.objects.append(obj)

# Initialize the model builder
builder = ModelBuilder()

# Create the components
builder.add_cylinder(0.5, 1.0, (0, 0, 0.5), name='Container')
builder.add_cylinder(0.05, 0.3, (0.5, 0, 0.25), (0, math.pi/2, 0), name='Perch')
builder.add_cone(0.6, 0.3, (0, 0, 1.15), name='Roof')
builder.add_torus(0.1, 0.02, (0, 0, 1.3), (math.pi/2, 0, 0), name='Hook')
