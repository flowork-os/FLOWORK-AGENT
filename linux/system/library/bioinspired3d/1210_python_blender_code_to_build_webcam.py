# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_build_webcam" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to build webcam

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a spherical camera
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 0.5))
camera_entity = bpy.context.object
camera_entity.name = 'Camera'

# Generate a cylindrical mount
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(0, 0, 0.25))
mount_entity = bpy.context.object
mount_entity.name = 'Mount'

# Construct the cylindrical base
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.1, location=(0, 0, 0))
base_entity = bpy.context.object
base_entity.name = 'Base'
