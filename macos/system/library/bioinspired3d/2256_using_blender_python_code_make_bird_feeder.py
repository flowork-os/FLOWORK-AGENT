# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_python_code_make_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender python code make bird feeder

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def add_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

def add_cone(radius, depth, location, name):
    bpy.ops.mesh.primitive_cone_add(radius1=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

main_structure = add_cylinder(0.5, 1.0, (0, 0, 0.5), 'Base')
roof_structure = add_cone(0.6, 0.3, (0, 0, 1.15), 'Top')

perch_structure = add_cylinder(0.05, 0.8, (0.5, 0, 0.3), 'Bird Perch')
perch_structure.rotation_euler = (0, math.pi / 2, 0)
