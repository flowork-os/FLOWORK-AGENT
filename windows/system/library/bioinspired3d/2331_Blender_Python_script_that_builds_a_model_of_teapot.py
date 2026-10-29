# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_builds_a_model_of_teapot" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that builds a model of teapot

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_mesh(shape, **kwargs):
    if shape == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(**kwargs)
    elif shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(**kwargs)
    elif shape == 'torus':
        bpy.ops.mesh.primitive_torus_add(**kwargs)

create_mesh('sphere', radius=1, location=(0, 0, 0))
main_body = bpy.context.object
main_body.name = 'Teapot Main Body'

create_mesh('cylinder', radius=0.1, depth=0.8, location=(1.2, 0, 0.3), rotation=(0, math.pi / 4, 0))
spout = bpy.context.object
spout.name = 'Teapot Spout'

create_mesh('torus', major_radius=0.6, minor_radius=0.1, location=(-1.2, 0, 0.3), rotation=(math.pi / 2, 0, 0))
handle = bpy.context.object
handle.name = 'Teapot Handle'

create_mesh('cylinder', radius=0.5, depth=0.2, location=(0, 0, 1.1))
lid = bpy.context.object
lid.name = 'Teapot Lid'

create_mesh('sphere', radius=0.1, location=(0, 0, 1.3))
knob = bpy.context.object
knob.name = 'Teapot Lid Knob'
