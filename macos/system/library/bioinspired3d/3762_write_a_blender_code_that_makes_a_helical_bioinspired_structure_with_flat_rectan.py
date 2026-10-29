# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_blender_code_that_makes_a_helical_bioinspired_structure_with_flat_rectan" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a blender code that makes a helical bioinspired structure with flat rectangular struts in each layer. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

layer_num = 15  # Number of layers in the structure
rotation_increment = 3  # Rotation angle in degrees for each layer
fiber_form = 'rect'  # Shape of fibers

full_height = 2.0  # Total height of the structure
plate_dim = 2.0  # Width and length of each square plate
thickness_per_layer = full_height / layer_num  # Thickness of each layer
fiber_space = 0.01  # Space between fibers

def add_fiber(form, diameter, position):
    if form == 'rect':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=position, rotation=(0, math.radians(90), 0))
        fiber_object = bpy.context.object
        fiber_object.dimensions = (thickness_per_layer, diameter, plate_dim)
        return fiber_object

def generate_layer(index):
    z_coord = index * thickness_per_layer
    rotation_angle = index * rotation_increment

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    empty_object = bpy.context.object

    fiber_diameter = thickness_per_layer
    spacing = fiber_diameter + fiber_space
    fiber_count = max(1, int(plate_dim / spacing))

    total_space = fiber_count * spacing
    start_y = -plate_dim / 2 + spacing / 2 + (plate_dim - total_space) / 2

    for i in range(fiber_count):
        current_y = start_y + i * spacing
        fiber_instance = add_fiber(
            form=fiber_form,
            diameter=fiber_diameter,
            position=(0, current_y, z_coord)
        )
        fiber_instance.parent = empty_object
        fiber_instance.matrix_parent_inverse = empty_object.matrix_world.inverted()

    empty_object.rotation_euler[2] = math.radians(rotation_angle)
    return empty_object

for i in range(layer_num):
    generate_layer(i)
