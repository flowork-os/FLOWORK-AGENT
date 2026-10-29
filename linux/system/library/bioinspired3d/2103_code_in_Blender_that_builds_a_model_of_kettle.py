# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_builds_a_model_of_kettle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that builds a model of kettle.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_mesh(primitive_type, **kwargs):
    if primitive_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(**kwargs)
    elif primitive_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(**kwargs)
    elif primitive_type == 'torus':
        bpy.ops.mesh.primitive_torus_add(**kwargs)

create_mesh('sphere', radius=1, location=(0, 0, 0))
kettle_body = bpy.context.object
kettle_body.name = 'Kettle Main'

create_mesh('cylinder', radius=0.1, depth=0.6, location=(1.1, 0, 0.3), rotation=(0, math.pi / 4, 0))
spout = bpy.context.object
spout.name = 'Spout'

create_mesh('torus', major_radius=1.2, minor_radius=0.1, location=(-0.8, 0, 0.8), rotation=(math.pi / 2, 0, 0))
handle = bpy.context.object
handle.name = 'Handle'

create_mesh('cylinder', radius=0.6, depth=0.2, location=(0, 0, 1.1))
lid = bpy.context.object
lid.name = 'Lid'
