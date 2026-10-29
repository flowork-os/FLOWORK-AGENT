# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_script_that_creates_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender script that creates a model of bird feeder.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0, location=(0, 0, 0.5))
base = bpy.context.object
base.name = 'Base Structure'

bpy.ops.mesh.primitive_cone_add(radius1=0.6, depth=0.3, location=(0, 0, 1.15))
roof_part = bpy.context.object
roof_part.name = 'Roof Part'

bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.8, location=(0.5, 0, 0.3), rotation=(0, math.pi/2, 0))
perch_part = bpy.context.object
perch_part.name = 'Perch Cylinder'
