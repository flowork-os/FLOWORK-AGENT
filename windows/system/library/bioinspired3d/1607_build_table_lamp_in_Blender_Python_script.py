# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_table_lamp_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build table lamp in Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_cylinder(radius, depth, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    return obj

base_component = create_cylinder(1, 0.2, (0, 0, 0.1), 'Lamp_Base')
pole_component = create_cylinder(0.1, 3, (0, 0, 1.6), 'Lamp_Pole')
lampshade_component = create_cylinder(0.8, 1, (0, 0, 3.6), 'Lamp_Lampshade')
pull_chain_component = create_cylinder(0.02, 1.5, (0.1, 0, 2.25), 'Lamp_Pull_Chain')
pull_chain_component.rotation_euler = (0, 0, math.radians(90))
