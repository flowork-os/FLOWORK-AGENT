# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_script_make_star_symbol" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender script make star symbol

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Star creation function

def create_star_shape():
    vertex_coords = [
        (0, 1, 0),
        (0.2245, 0.309, 0),
        (0.9511, 0.309, 0),
        (0.3633, -0.118, 0),
        (0.5878, -0.809, 0),
        (0, -0.382, 0),
        (-0.5878, -0.809, 0),
        (-0.3633, -0.118, 0),
        (-0.9511, 0.309, 0),
        (-0.2245, 0.309, 0),
    ]
    face_indices = [
        (0, 1, 3, 5, 7, 9),
        (1, 2, 3),
        (3, 4, 5),
        (5, 6, 7),
        (7, 8, 9),
        (9, 0, 1),
    ]

    mesh = bpy.data.meshes.new(name="StarModel")
    star_object = bpy.data.objects.new(name="StarMeshObject", object_data=mesh)
    bpy.context.collection.objects.link(star_object)
    mesh.from_pydata(vertex_coords, [], face_indices)
    mesh.update()
    star_object.location = (0, 0, 0)

create_star_shape()
