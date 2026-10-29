# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_table_lamp_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make table lamp using Blender Python script

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the base for the lamp
base = create_cylinder(0.3, 0.05, (0, 0, 0), 'Lamp_Base')

# Create the main body of the lamp
lamp_body = create_cylinder(0.15, 1, (0, 0, 0.5), 'Lamp_Body')

# Create the shade of the lamp using a cone
bpy.ops.mesh.primitive_cone_add(radius1=0.3, depth=0.7, location=(0, 0, 1.35))
shade = bpy.context.object
shade.name = 'Lamp_Shade'

# Add a switch to the lamp
bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0.25, 0, 0.1))
switch = bpy.context.object
switch.name = 'Lamp_Switch'
