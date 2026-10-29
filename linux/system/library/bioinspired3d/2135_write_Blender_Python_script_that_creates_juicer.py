# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_Python_script_that_creates_juicer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender Python script that creates juicer

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

def create_cone(radius_top, radius_bottom, depth, location, name):
    bpy.ops.mesh.primitive_cone_add(radius1=radius_top, radius2=radius_bottom, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

body = create_cylinder(1, 2, (0, 0, 1), 'CylindricalBody')
cone = create_cone(1, 0, 1, (0, 0, 2.5), 'ConicalTop')
spout = create_cylinder(0.1, 0.5, (1, 0, 1), 'Spout')
spout.rotation_euler = (0, math.pi / 2, 0)
