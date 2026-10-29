# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_cone_ontop_of_a_cylinder_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of cone ontop of a cylinder in blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))

# Create a cone
bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 3))

# Optionally, you can join the two objects into one
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects['Cylinder'].select_set(True)
bpy.data.objects['Cone'].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['Cylinder']
bpy.ops.object.join()
