# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender__construct_webcam" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender, construct webcam

import bpy

# Clear existing objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a sphere for the camera
def add_camera(location):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=location)
    camera_obj = bpy.context.object
    camera_obj.name = 'Camera'

# Function to create the mount
def add_mount(location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=location)
    mount_obj = bpy.context.object
    mount_obj.name = 'Mount'

# Function to create the base
def add_base(location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.1, location=location)
    base_obj = bpy.context.object
    base_obj.name = 'Base'

# Create objects at specified locations
add_camera((0, 0, 0.5))
add_mount((0, 0, 0.25))
add_base((0, 0, 0))
