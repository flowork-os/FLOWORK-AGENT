# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_code__generate_table_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender code, generate table lamp.

import bpy

# Remove existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a custom class for lamp components
class LampComponent:
    def __init__(self, radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        self.obj = bpy.context.object
        self.obj.name = name

# Create the base, stand, and lampshade using the LampComponent class
base = LampComponent(0.5, 0.1, (0, 0, 0.05), "Base")
stand = LampComponent(0.05, 1, (0, 0, 0.6), "Stand")
lampshade = LampComponent(0.4, 0.6, (0, 0, 1.3), "Lampshade")

# Function to add a hole in the lampshade
def add_hole(radius, z_position):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=0.01, location=(0, 0, z_position))
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='ONLY_FACE')
    bpy.ops.object.mode_set(mode='OBJECT')

# Create holes at the top and bottom of the lampshade
add_hole(0.3, 1.6)
add_hole(0.3, 1.0)

# Combine the lampshade and openings
bpy.ops.object.select_all(action='DESELECT')
lampshade.obj.select_set(True)
bpy.ops.object.join()
