# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_Python_script_construct_a_helical_Bouligand_material_where_each_pl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender Python script construct a helical Bouligand material where each ply consists of cylindrical fibers Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Number of layers in the structure
angle_per_layer = 15  # Rotation angle in degrees for each layer
fiber_type = 'cylinder'  # Type of fiber shape

# Dimensions of the entire structure
structure_height = 2  # Total height of the structure
plate_dimension = 2  # Width and length of each square plate
layer_thickness = structure_height / layers_count  # Thickness of each layer

def create_fiber(shape, diameter, pos_x, pos_y, pos_z):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(pos_x, pos_y, pos_z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def build_layer(layer_index):
    height_offset = layer_index * layer_thickness
    rotation_angle = layer_index * angle_per_layer

    # Create a parent object for fibers
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, height_offset))
    layer_empty = bpy.context.object

    fiber_radius = layer_thickness
    total_fibers = max(1, int(plate_dimension / fiber_radius))

    fiber_spacing = total_fibers * fiber_radius
    extra_space = plate_dimension - fiber_spacing
    initial_y = -plate_dimension / 2 + (fiber_radius / 2) + (extra_space / 2)

    for j in range(total_fibers):
        fiber_y_position = initial_y + j * fiber_radius
        fiber_instance = create_fiber(
            shape=fiber_type,
            diameter=fiber_radius,
            pos_x=0,
            pos_y=fiber_y_position,
            pos_z=height_offset
        )
        fiber_instance.parent = layer_empty
        fiber_instance.location = (0, fiber_y_position, 0)

    # Activate the layer_empty for rotation
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = layer_empty
    layer_empty.select_set(True)

    bpy.ops.transform.rotate(
        value=math.radians(rotation_angle),
        orient_axis='Z'
    )

    return layer_empty

# Construct the entire structure
for k in range(layers_count):
    build_layer(k)
