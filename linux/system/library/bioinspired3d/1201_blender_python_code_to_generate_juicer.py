# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_generate_juicer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to generate juicer

import bpy
import math

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the main components of the object
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
main_body = bpy.context.object
main_body.name = 'MainBody'

bpy.ops.mesh.primitive_cone_add(radius1=1, radius2=0, depth=1, location=(0, 0, 2.5))
cone_top = bpy.context.object
cone_top.name = 'ConeTop'

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(1, 0, 1))
water_spout = bpy.context.object
water_spout.name = 'WaterSpout'
water_spout.rotation_euler = (0, math.pi / 2, 0)

# Grouping the objects for better organization
bpy.ops.object.select_all(action='DESELECT')
main_body.select_set(True)
cone_top.select_set(True)
water_spout.select_set(True)
bpy.context.view_layer.objects.active = main_body
bpy.ops.object.parent_set(type='OBJECT')
