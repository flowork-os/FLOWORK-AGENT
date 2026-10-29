# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_helical_Bouligand_material_with_each_layer_composed_of_aligned_cylinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a helical Bouligand material with each layer composed of aligned cylinders in blender python code think step by step.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for helical fiber arrangement
ply_count = 12  # Total number of plies
rotation_angle = 15  # Rotation degree for each ply
fiber_shape = 'cylinder'  # Fiber shape type

# Dimensions of the helical structure
structure_height = 2  # Total height
plate_dimension = 2  # Each plate's width and length
ply_thickness = structure_height / ply_count  # Thickness of each ply

def create_fiber(shape, diameter, x, y, z):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def add_layer(layer_index):
    z_position = layer_index * ply_thickness
    rotation_value = layer_index * rotation_angle

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = ply_thickness
    total_fibers = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = total_fibers * fiber_diameter
    remaining_space = plate_dimension - total_fiber_space
    initial_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(total_fibers):
        fiber_y = initial_y + i * fiber_diameter
        fiber_object = create_fiber(
            shape=fiber_shape,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y,
            z=z_position
        )
        fiber_object.parent = layer_empty
        fiber_object.location = (0, fiber_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)
    bpy.ops.transform.rotate(
        value=math.radians(rotation_value),
        orient_axis='Z'
    )
    return layer_empty

# Build the helical structure
for layer in range(ply_count):
    add_layer(layer)
