# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_script__make_a_helical_Bouligand_bioinspired_material_made_of_cylin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender script, make a helical Bouligand bioinspired material made of cylindrical fibers. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 5  # Degrees of rotation for each layer
fiber_type = 'cylinder'  # Type of fiber

# Dimensions of the overall structure
structure_height = 2
plate_dimension = 2
layer_thickness = structure_height / layers_count

def create_fiber(shape, diameter, pos_x, pos_y, pos_z):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(pos_x, pos_y, pos_z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

for layer in range(layers_count):
    z_position = layer * layer_thickness
    rotation_angle = layer * angle_per_layer

    # Create a parent object for the fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    fiber_group = bpy.context.object

    fiber_diameter = layer_thickness
    count_of_fibers = max(1, int(plate_dimension / fiber_diameter))

    space_for_fibers = count_of_fibers * fiber_diameter
    remaining_space = plate_dimension - space_for_fibers
    initial_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(count_of_fibers):
        fiber_y_position = initial_y + i * fiber_diameter
        new_fiber = create_fiber(
            shape=fiber_type,
            diameter=fiber_diameter,
            pos_x=0,
            pos_y=fiber_y_position,
            pos_z=z_position
        )
        new_fiber.parent = fiber_group
        new_fiber.location = (0, fiber_y_position, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = fiber_group
    fiber_group.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
