# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_teapot_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build teapot using Blender Python script

import bpy
import math

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to add a mesh with specific parameters

def add_mesh(mesh_type, params):
    if mesh_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(**params)
    elif mesh_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(**params)
    elif mesh_type == 'torus':
        bpy.ops.mesh.primitive_torus_add(**params)

# Create the teapot body
add_mesh('sphere', {'radius': 1, 'location': (0, 0, 0)})

# Create the spout
add_mesh('cylinder', {'radius': 0.1, 'depth': 0.8, 'location': (1.2, 0, 0.3), 'rotation': (0, math.pi / 4, 0)})

# Create the handle
add_mesh('torus', {'major_radius': 0.6, 'minor_radius': 0.1, 'location': (-1.2, 0, 0.3), 'rotation': (math.pi / 2, 0, 0)})

# Create the lid
add_mesh('cylinder', {'radius': 0.5, 'depth': 0.2, 'location': (0, 0, 1.1)})

# Create the knob on the lid
add_mesh('sphere', {'radius': 0.1, 'location': (0, 0, 1.3)})
