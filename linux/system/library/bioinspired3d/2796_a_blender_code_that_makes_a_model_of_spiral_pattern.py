# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_makes_a_model_of_spiral_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that makes a model of spiral pattern

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_spiral(turns, points_per_turn, sphere_radius, height_increment):
    total_points = turns * points_per_turn
    for i in range(total_points):
        theta = i * (2 * math.pi / points_per_turn)
        x_coord = sphere_radius * theta * math.cos(theta)
        y_coord = sphere_radius * theta * math.sin(theta)
        z_coord = height_increment * (i / points_per_turn)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_coord, y_coord, z_coord))

spiral_turns = 5
points_each_turn = 50
spiral_radius = 0.1
vertical_height = 0.1

create_spiral(spiral_turns, points_each_turn, spiral_radius, vertical_height)
