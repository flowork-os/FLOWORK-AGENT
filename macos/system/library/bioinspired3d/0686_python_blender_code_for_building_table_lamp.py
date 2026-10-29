# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_building_table_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for building table lamp.

import bpy
import math

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to add a cylinder with given parameters

def add_cylinder(radius, height, position, obj_name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    cylinder = bpy.context.object
    cylinder.name = obj_name
    return cylinder

# Create lamp components
add_cylinder(1, 0.2, (0, 0, 0.1), 'Base')
add_cylinder(0.1, 3, (0, 0, 1.6), 'Pole')
add_cylinder(0.8, 1, (0, 0, 3.6), 'Lampshade')
pull_chain = add_cylinder(0.02, 1.5, (0.1, 0, 2.25), 'Pull_Chain')
pull_chain.rotation_euler = (0, 0, math.radians(90))
