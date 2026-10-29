# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_constructs_a_helical_material_with_each_layer_composed_of_al" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that constructs a helical material with each layer composed of aligned cylinders think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Helical fiber structure configuration
layers_total = 9  # Total number of layers
rotation_increment = 8  # Degrees of rotation per layer
fiber_shape = 'cylinder'  # Fiber shape type

# Structure dimensions
entire_height = 2  # Total height of the structure
plate_dimension = 2  # Size of each square plate
layer_thickness = entire_height / layers_total  # Thickness of each layer

# Function to create fibers
def make_fiber(shape, diameter, x, y, z):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

# Function to create a layer of fibers
def create_fiber_layer(index):
    z_coord = index * layer_thickness
    angle = index * rotation_increment

    # Create empty object for the layer
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    total_space = fiber_count * fiber_radius
    extra_space = plate_dimension - total_space
    start_y = -plate_dimension / 2 + (fiber_radius / 2) + (extra_space / 2)

    for i in range(fiber_count):
        fiber_y = start_y + i * fiber_radius
        fiber_instance = make_fiber(
            shape=fiber_shape,
            diameter=fiber_radius,
            x=0,
            y=fiber_y,
            z=z_coord
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(angle),
        orient_axis='Z'
    )

# Create the helical structure
for i in range(layers_total):
    create_fiber_layer(i)
