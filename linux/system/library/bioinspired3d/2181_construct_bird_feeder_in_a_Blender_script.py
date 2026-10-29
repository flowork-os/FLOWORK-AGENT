# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_bird_feeder_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct bird feeder in a Blender script

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0, location=(0, 0, 0.5))
container = bpy.context.object
container.name = 'MainContainer'

bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.3, location=(0.5, 0, 0.25), rotation=(0, math.pi/2, 0))
perch = bpy.context.object
perch.name = 'SupportPerch'

bpy.ops.mesh.primitive_cone_add(radius1=0.6, depth=0.3, location=(0, 0, 1.15))
roof = bpy.context.object
roof.name = 'TopRoof'

bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.02, location=(0, 0, 1.3), rotation=(math.pi/2, 0, 0))
hook = bpy.context.object
hook.name = 'HangingHook'

hook.scale = (1.0, 1.0, 1.0)
