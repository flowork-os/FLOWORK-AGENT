# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_table_lamp_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of table lamp using python blender code

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create lamp components
components = []

# Base creation
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.05, location=(0, 0, 0))
components.append(bpy.context.object)
components[-1].name = 'Lamp_Base'

# Body creation
bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1, location=(0, 0, 0.5))
components.append(bpy.context.object)
components[-1].name = 'Lamp_Body'

# Shade creation
bpy.ops.mesh.primitive_cone_add(radius1=0.3, depth=0.7, location=(0, 0, 1.35))
components.append(bpy.context.object)
components[-1].name = 'Lamp_Shade'

# Switch creation
bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0.25, 0, 0.1))
components.append(bpy.context.object)
components[-1].name = 'Lamp_Switch'
