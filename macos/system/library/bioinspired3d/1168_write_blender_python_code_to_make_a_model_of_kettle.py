# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_python_code_to_make_a_model_of_kettle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender python code to make a model of kettle.

import bpy
import math

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to add a kettle

def add_kettle():
    # Main body creation
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
    kettle_body = bpy.context.object
    kettle_body.name = 'Kettle'

    # Adding spout
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.6, location=(1.1, 0, 0.3), rotation=(0, math.pi / 4, 0))
    spout = bpy.context.object
    spout.name = 'Spout'

    # Adding handle
    bpy.ops.mesh.primitive_torus_add(major_radius=1.2, minor_radius=0.1, location=(-0.8, 0, 0.8), rotation=(math.pi / 2, 0, 0))
    handle = bpy.context.object
    handle.name = 'Handle'

    # Adding lid
    bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=0.2, location=(0, 0, 1.1))
    lid = bpy.context.object
    lid.name = 'Lid'

# Call the function to create the kettle
add_kettle()
