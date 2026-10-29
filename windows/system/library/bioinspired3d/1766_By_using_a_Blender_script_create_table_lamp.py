# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_create_table_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script create table lamp.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to add a cylinder with specified parameters
def add_cylinder(radius, depth, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the base of the lamp
base_cylinder = add_cylinder(0.5, 0.1, (0, 0, 0.05), "LampBase")

# Create the vertical stand
stand_cylinder = add_cylinder(0.05, 1, (0, 0, 0.6), "LampStand")

# Create the lampshade
lampshade_cylinder = add_cylinder(0.4, 0.6, (0, 0, 1.3), "Lampshade")

# Function to create openings in the lampshade
def create_opening(radius, position):
    opening = add_cylinder(radius, 0.01, position, "Opening")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='ONLY_FACE')
    bpy.ops.object.mode_set(mode='OBJECT')
    return opening

# Create openings at the top and bottom of the lampshade
create_opening(0.3, (0, 0, 1.6))
create_opening(0.3, (0, 0, 1))

# Join the lampshade and its openings
bpy.ops.object.select_all(action='DESELECT')
lampshade_cylinder.select_set(True)
bpy.ops.object.join()
