# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_code__construct_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender code, construct bird feeder.

import bpy

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

# Create the main structure
body = create_cylinder(0.3, 1, (0, 0, 0.5), 'MainBody')
base = create_cylinder(0.35, 0.05, (0, 0, 0.025), 'Foundation')

# Create the top part
bpy.ops.mesh.primitive_cone_add(radius1=0.4, depth=0.2, location=(0, 0, 1.1))
roof = bpy.context.object
roof.name = 'Top'
