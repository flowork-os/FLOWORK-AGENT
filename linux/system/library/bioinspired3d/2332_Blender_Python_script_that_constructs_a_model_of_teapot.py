# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_constructs_a_model_of_teapot" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that constructs a model of teapot.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class Teapot:
    def __init__(self):
        self.create_body()
        self.create_spout()
        self.create_handle()
        self.create_lid()
        self.create_knob()

    def create_body(self):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
        body = bpy.context.object
        body.name = 'Teapot Body'

    def create_spout(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.8, location=(1.2, 0, 0.3), rotation=(0, math.pi / 4, 0))
        spout = bpy.context.object
        spout.name = 'Teapot Spout'

    def create_handle(self):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.1, location=(-1.2, 0, 0.3), rotation=(math.pi / 2, 0, 0))
        handle = bpy.context.object
        handle.name = 'Teapot Handle'

    def create_lid(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.2, location=(0, 0, 1.1))
        lid = bpy.context.object
        lid.name = 'Teapot Lid'

    def create_knob(self):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 1.3))
        knob = bpy.context.object
        knob.name = 'Teapot Lid Knob'

Teapot()
