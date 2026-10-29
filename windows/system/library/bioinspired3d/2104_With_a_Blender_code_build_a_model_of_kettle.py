# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code_build_a_model_of_kettle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code build a model of kettle.

import bpy
import math

# Reset the Blender scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create kettle components using a class
class Kettle:
    def __init__(self):
        self.create_body()
        self.create_spout()
        self.create_handle()
        self.create_lid()

    def create_body(self):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
        body = bpy.context.object
        body.name = 'Main Body'

    def create_spout(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.6, location=(1.1, 0, 0.3), rotation=(0, math.pi / 4, 0))
        spout = bpy.context.object
        spout.name = 'Spout'

    def create_handle(self):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.2, minor_radius=0.1, location=(-0.8, 0, 0.8), rotation=(math.pi / 2, 0, 0))
        handle = bpy.context.object
        handle.name = 'Handle'

    def create_lid(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=0.2, location=(0, 0, 1.1))
        lid = bpy.context.object
        lid.name = 'Lid'

# Instantiate the kettle
Kettle()
