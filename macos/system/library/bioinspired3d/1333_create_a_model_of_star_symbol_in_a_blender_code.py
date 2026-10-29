# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_star_symbol_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of star symbol in a blender code

import bpy
import math

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a star shape

def create_star():
    star_points = [
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
    star_faces = [
        (0, 1, 3, 5, 7, 9),
        (1, 2, 3),
        (3, 4, 5),
        (5, 6, 7),
        (7, 8, 9),
        (9, 0, 1),
    ]

    mesh_data = bpy.data.meshes.new(name="StarShape")
    star_object = bpy.data.objects.new(name="StarObject", object_data=mesh_data)
    bpy.context.collection.objects.link(star_object)
    mesh_data.from_pydata(star_points, [], star_faces)
    mesh_data.update()
    star_object.location = (0, 0, 0)

create_star()
