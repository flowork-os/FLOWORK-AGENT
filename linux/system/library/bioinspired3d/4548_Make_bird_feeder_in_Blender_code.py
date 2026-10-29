# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_bird_feeder_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make bird feeder in Blender code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder
def create_cylinder(radius, depth, location, rotation=(0, 0, 0), name=''):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return obj

# Step 1: Build the Seed Tube
seed_tube = create_cylinder(0.4, 1, (0, 0, 0.5), name='Seed Tube')

# Step 2: Build the Perch
perch = create_cylinder(0.05, 0.8, (0, 0.4, 0.1), rotation=(1.57, 0, 0), name='Perch')

# Step 3: Create the Roof using a cone
bpy.ops.mesh.primitive_cone_add(radius1=0.4, radius2=0.1, depth=0.3, location=(0, 0, 1.15))
roof = bpy.context.object
roof.name = 'Roof'

# Step 4: Add the Hook using a torus
bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.01, location=(0, 0, 1.35), rotation=(1.57, 0, 0))
hook = bpy.context.object
hook.name = 'Hanging Hook'
