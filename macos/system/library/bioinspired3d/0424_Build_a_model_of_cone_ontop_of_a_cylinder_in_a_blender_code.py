# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_cone_ontop_of_a_cylinder_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of cone ontop of a cylinder in a blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
cylinder = bpy.context.object

# Create a cone
bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 3))
cone = bpy.context.object

# Optionally, you can join the cone and cylinder into a single object
bpy.ops.object.select_all(action='DESELECT')
cylinder.select_set(True)
cone.select_set(True)
bpy.context.view_layer.objects.active = cylinder
bpy.ops.object.join()
