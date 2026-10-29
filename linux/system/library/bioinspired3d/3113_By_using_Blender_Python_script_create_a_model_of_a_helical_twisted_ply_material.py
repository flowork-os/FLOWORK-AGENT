# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script_create_a_model_of_a_helical_twisted_ply_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script create a model of a helical twisted ply material made of cylindrical fibers

import bpy
import math

# Remove all objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber arrangement
layers = 8  # Number of layers in the helical structure
rotation_step = 10  # Degrees of rotation for each layer
fiber_form = 'cylinder'  # Shape of the fibers

# Overall dimensions of the structure
structure_height = 2.0  # Height of the entire structure
plate_dimension = 2.0  # Dimensions of the plates
layer_height = structure_height / layers  # Height of each layer

def add_cylinder(fiber_form, diameter, x, y, z):
    if fiber_form == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def create_layer(layer_index):
    z_position = layer_index * layer_height
    layer_rotation = layer_index * rotation_step

    # Create an empty object to hold the fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_radius = layer_height
    fiber_count = max(1, int(plate_dimension / fiber_radius))

    total_width = fiber_count * fiber_radius
    free_space = plate_dimension - total_width
    start_y = -plate_dimension / 2 + (fiber_radius / 2) + (free_space / 2)

    for i in range(fiber_count):
        fiber_center_y = start_y + i * fiber_radius
        fiber = add_cylinder(
            fiber_form=fiber_form,
            diameter=fiber_radius,
            x=0,
            y=fiber_center_y,
            z=z_position
        )
        fiber.parent = layer_empty
        fiber.location = (0, fiber_center_y, 0)

    # Set the empty object as active for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(layer_rotation),
        orient_axis='Z'
    )

    return layer_empty

# Build the helical structure
for index in range(layers):
    create_layer(index)
