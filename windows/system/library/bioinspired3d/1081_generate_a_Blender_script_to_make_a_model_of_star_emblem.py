# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_script_to_make_a_model_of_star_emblem" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender script to make a model of star emblem.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a star shape

def create_star(num_points, outer_rad, inner_rad, angle_offset):
    points = []
    for i in range(num_points * 2):
        theta = i * math.pi / num_points + angle_offset
        rad = outer_rad if i % 2 == 0 else inner_rad
        x = rad * math.cos(theta)
        y = rad * math.sin(theta)
        points.append((x, y, 0))
    return points

# Parameters for the star
star_points = create_star(5, 1, 0.5, math.pi / 2)

# Create the mesh for the star
star_mesh = bpy.data.meshes.new(name='StarMesh')
star_mesh.from_pydata(star_points, [], [(i, (i + 1) % (10), (i + 2) % (10)) for i in range(0, 10, 2)])
star_mesh.update()

# Create the star object and link to the current collection
star_object = bpy.data.objects.new('StarObject', star_mesh)
bpy.context.collection.objects.link(star_object)
