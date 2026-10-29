# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_blender_code__make_a_model_of_a_helical_Bouligand_bioinspired_material_w" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a blender code, make a model of a helical Bouligand bioinspired material with each layer formed by rectangular fibers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ply_count = 12
angle_per_ply = 10
fiber_form = 'rect'

structure_total_height = 2.0
individual_plate_size = 2.0
thickness_of_each_ply = structure_total_height / ply_count
fiber_distance = 0.01

def add_fiber(form, diameter, x_coord, y_coord, z_coord, thickness):
    if form == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_coord, y_coord, z_coord), rotation=(0, math.radians(90), 0))
        fiber = bpy.context.object
        fiber.dimensions = (thickness, diameter, individual_plate_size)
        return fiber

def create_ply(index):
    z_coord = index * thickness_of_each_ply
    rotation_angle = index * angle_per_ply

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    empty_object = bpy.context.object

    fiber_diameter = thickness_of_each_ply
    spacing = fiber_diameter + fiber_distance
    fiber_count = max(1, int(individual_plate_size / spacing))

    total_fiber_width = fiber_count * spacing
    start_y_coord = -individual_plate_size / 2 + spacing / 2 + (individual_plate_size - total_fiber_width) / 2

    for i in range(fiber_count):
        fiber_y_coord = start_y_coord + i * spacing
        fiber_instance = add_fiber(fiber_form, fiber_diameter, 0, fiber_y_coord, z_coord, thickness_of_each_ply)
        fiber_instance.parent = empty_object
        fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(rotation_angle)
    return empty_object

for i in range(ply_count):
    create_ply(i)
