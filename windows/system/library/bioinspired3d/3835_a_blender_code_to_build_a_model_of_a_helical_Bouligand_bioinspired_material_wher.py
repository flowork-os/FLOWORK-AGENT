# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_build_a_model_of_a_helical_Bouligand_bioinspired_material_wher" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to build a model of a helical Bouligand bioinspired material where each ply consists of cylindrical fibers Think step by step

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber assembly
ply_count = 8
rotation_step = 15
fiber_shape_type = 'cylinder'

# Dimensions for the helical structure
height_total = 2
plate_dimension = 2
thickness_per_ply = height_total / ply_count

def generate_fiber(shape, diameter, position):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=position,
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

for index in range(ply_count):
    z_position = index * thickness_per_ply
    rotation_angle = index * rotation_step

    # Create a parent empty object for the fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    parent_object = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_length = fiber_count * fiber_diameter
    excess_space = plate_dimension - total_fiber_length
    starting_y = -plate_dimension / 2 + (fiber_diameter / 2) + (excess_space / 2)

    for i in range(fiber_count):
        fiber_y_position = starting_y + i * fiber_diameter
        fiber_instance = generate_fiber(
            shape=fiber_shape_type,
            diameter=fiber_diameter,
            position=(0, fiber_y_position, z_position)
        )
        fiber_instance.parent = parent_object
        fiber_instance.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = parent_object
    parent_object.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
