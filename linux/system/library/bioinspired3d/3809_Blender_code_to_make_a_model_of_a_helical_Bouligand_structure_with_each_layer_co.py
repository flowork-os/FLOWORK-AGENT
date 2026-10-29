# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_make_a_model_of_a_helical_Bouligand_structure_with_each_layer_co" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to make a model of a helical Bouligand structure with each layer composed of aligned cylinders Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_layers = 7  # Number of layers
rotation_step = 10  # Rotation step in degrees
fiber_form = 'cylinder'  # Shape of fibers

height_of_structure = 2  # Total height
plate_dimension = 2  # Size of plates
thickness_of_layer = height_of_structure / num_layers  # Layer thickness

def generate_fiber(fiber_form, diameter, x, y, z):
    if fiber_form == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

def create_fiber_layer(layer_index):
    z_position = layer_index * thickness_of_layer
    angle = layer_index * rotation_step

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    layer_empty = bpy.context.object

    fiber_diameter = thickness_of_layer
    total_fibers = max(1, int(plate_dimension / fiber_diameter))

    total_space = total_fibers * fiber_diameter
    remaining_space = plate_dimension - total_space
    initial_y = -plate_dimension / 2 + (fiber_diameter / 2) + (remaining_space / 2)

    for i in range(total_fibers):
        fiber_y = initial_y + i * fiber_diameter
        fiber_object = generate_fiber(
            fiber_form=fiber_form,
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
        value=math.radians(angle),
        orient_axis='Z'
    )

for index in range(num_layers):
    create_fiber_layer(index)
