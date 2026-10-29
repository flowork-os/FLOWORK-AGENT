# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_blender_code_that_makes_a_model_of_a_helical_Bouligand_bioinspired_materi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a blender code that makes a model of a helical Bouligand bioinspired material made of cylindrical fibers. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the helical fiber structure
layers = 8  # Number of layers in the structure
angle_step = 20  # Rotation angle for each layer
fiber_shape_type = 'cylinder'  # Shape of fibers

# Dimensions of the overall structure
complete_height = 2.0  # Total height of the structure
plate_dimension = 2.0  # Width and length of each square plate
layer_height = complete_height / layers  # Height of each layer

def create_fiber(shape, diameter, x, y, z):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def assemble_layer(index):
    z_coord = index * layer_height
    rotation_angle = index * angle_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_coord))
    layer_empty = bpy.context.object

    fiber_diameter = layer_height
    fiber_count = max(1, int(plate_dimension / fiber_diameter))

    total_fiber_space = fiber_count * fiber_diameter
    extra_space = plate_dimension - total_fiber_space
    start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (extra_space / 2)

    for j in range(fiber_count):
        fiber_y_pos = start_y + j * fiber_diameter
        fiber_instance = create_fiber(
            shape=fiber_shape_type,
            diameter=fiber_diameter,
            x=0,
            y=fiber_y_pos,
            z=z_coord
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_pos, 0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Build the helical structure
for i in range(layers):
    assemble_layer(i)
