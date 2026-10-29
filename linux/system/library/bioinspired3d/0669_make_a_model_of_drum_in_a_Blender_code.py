# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_drum_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of drum in a Blender code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the drum components using different parameters
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
main_cylinder = bpy.context.object
main_cylinder.name = 'Drum Base'

bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 1.55))
head_cylinder = bpy.context.object
head_cylinder.name = 'Drum Top'
