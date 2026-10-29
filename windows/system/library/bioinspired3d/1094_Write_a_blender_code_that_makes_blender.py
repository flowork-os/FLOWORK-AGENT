# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_that_makes_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code that makes blender

import bpy

# Function to remove all mesh objects from the scene

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

# Create a new cylinder at a given position with specific dimensions

def add_cylinder(radius, height, coords, object_name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=coords)
    new_object = bpy.context.object
    new_object.name = object_name

# Main execution
clear_scene()
add_cylinder(1, 0.5, (0, 0, 0.25), 'Base')
add_cylinder(0.8, 2, (0, 0, 1.5), 'Jar')
add_cylinder(0.85, 0.2, (0, 0, 2.6), 'Lid')
