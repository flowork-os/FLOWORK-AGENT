# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_code_that_constructs_a_model_of_a_helical_twisted_ply_bioinspir" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender code that constructs a model of a helical twisted ply bioinspired structure with cylindrical rods forming each layer. think step by step.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber assembly
num_layers = 7  # Number of layers in the structure
rotation_increment = 10  # Incremental rotation per layer in degrees
fiber_shape_type = 'cylinder'  # Shape of the fibers

# Overall structure dimensions
structure_height = 2.0  # Total height of the structure
plate_dimension = 2.0  # Dimensions of each square plate
layer_thickness = structure_height / num_layers  # Thickness of each layer

def add_fiber(shape, diameter, x, y, z):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def create_layer(index):
    z_position = index * layer_thickness
    rotation_angle = index * rotation_increment

    # Create a parent empty object for the layer
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    fiber_spacing = fiber_count * fiber_diameter
    remaining_space = plate_dimension - fiber_spacing
    starting_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(fiber_count):
        fiber_y = starting_y + i * fiber_diameter
        fiber_instance = add_fiber(
            shape=fiber_shape_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y,
            z=z_position
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Build the helical structure
for i in range(num_layers):
    create_layer(i)
