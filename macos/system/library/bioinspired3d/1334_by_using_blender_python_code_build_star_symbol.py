# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_python_code_build_star_symbol" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender python code build star symbol.

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a function to build a star mesh

def build_star():
    points = [
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
    triangles = [
        (0, 1, 3, 5, 7, 9),
        (1, 2, 3),
        (3, 4, 5),
        (5, 6, 7),
        (7, 8, 9),
        (9, 0, 1),
    ]

    star_mesh = bpy.data.meshes.new(name="StarGeometry")
    star_obj = bpy.data.objects.new(name="StarShape", object_data=star_mesh)
    bpy.context.collection.objects.link(star_obj)
    star_mesh.from_pydata(points, [], triangles)
    star_mesh.update()
    star_obj.location = (0, 0, 0)

build_star()
