# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_that_creates_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script that creates a model of bird feeder

import bpy

# Clear the existing meshes in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Step 1: Add the Seed Tube
bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=1, location=(0, 0, 0.5))
seed_tube = bpy.context.object
seed_tube.name = 'Tube'

# Step 2: Add the Perch
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.8, location=(0, 0.4, 0.1), rotation=(1.57, 0, 0))
perch = bpy.context.object
perch.name = 'PerchBar'

# Step 3: Add the Roof
bpy.ops.mesh.primitive_cone_add(radius1=0.4, radius2=0.1, depth=0.3, location=(0, 0, 1.15))
roof = bpy.context.object
roof.name = 'FeederCap'

# Step 4: Add the Hook
bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.01, location=(0, 0, 1.35), rotation=(1.57, 0, 0))
hook = bpy.context.object
hook.name = 'FeederHook'
