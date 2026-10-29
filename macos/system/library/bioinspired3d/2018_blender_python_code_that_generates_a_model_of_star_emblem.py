# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_generates_a_model_of_star_emblem" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that generates a model of star emblem.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def build_star(num_pts, outer_rad, inner_rad, offset):
    vertices = []
    for i in range(num_pts * 2):
        angle = i * math.pi / num_pts + offset
        radius = outer_rad if i % 2 == 0 else inner_rad
        vertices.append((radius * math.cos(angle), radius * math.sin(angle), 0))
    return vertices

points = 5
outer_radius = 1.0
inner_radius = 0.5
angle_offset = math.pi / 2

star_vertices = build_star(points, outer_radius, inner_radius, angle_offset)

star_mesh = bpy.data.meshes.new('StarMesh')
star_mesh.from_pydata(star_vertices, [], [(i, (i + 1) % (10), (i + 2) % (10)) for i in range(0, 10, 2)])
star_mesh.update()

star_object = bpy.data.objects.new('StarObject', star_mesh)
bpy.context.collection.objects.link(star_object)
