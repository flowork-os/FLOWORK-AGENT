# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_make_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to make a model of bird feeder.

import bpy
import math

# Clear existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a mesh object

def create_mesh(shape, params, name):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params['radius'], depth=params['depth'], location=params['location'], rotation=params.get('rotation', (0, 0, 0)))
    elif shape == 'cone':
        bpy.ops.mesh.primitive_cone_add(radius1=params['radius'], depth=params['depth'], location=params['location'])
    elif shape == 'torus':
        bpy.ops.mesh.primitive_torus_add(major_radius=params['major_radius'], minor_radius=params['minor_radius'], location=params['location'], rotation=params.get('rotation', (0, 0, 0)))
    obj = bpy.context.object
    obj.name = name
    return obj

# Create main components
container_params = {'radius': 0.5, 'depth': 1.0, 'location': (0, 0, 0.5)}
create_mesh('cylinder', container_params, 'Container')

perch_params = {'radius': 0.05, 'depth': 0.3, 'location': (0.5, 0, 0.25), 'rotation': (0, math.pi/2, 0)}
create_mesh('cylinder', perch_params, 'Perch')

roof_params = {'radius': 0.6, 'depth': 0.3, 'location': (0, 0, 1.15)}
create_mesh('cone', roof_params, 'Roof')

hook_params = {'major_radius': 0.1, 'minor_radius': 0.02, 'location': (0, 0, 1.3), 'rotation': (math.pi/2, 0, 0)}
create_mesh('torus', hook_params, 'Hook')
