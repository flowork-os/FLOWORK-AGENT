# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_code_that_creates_a_model_of_a_helical_structure_made_of_cylindri" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender code that creates a model of a helical structure made of cylindrical fibers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the helical fiber structure
layers_count = 10  # Total number of layers
angle_per_layer = 15  # Degrees of rotation for each layer
fiber_type = 'cylinder'  # Type of fiber shape

# Dimensions of the structure
full_height = 2.0  # Complete height of the structure
plate_dimension = 2.0  # Width and length of each plate
layer_thickness = full_height / layers_count  # Thickness of each layer

def create_fiber(fiber_type, diameter, x, y, z):
    if fiber_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=diameter / 2,
            depth=plate_dimension,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)
        )
        return bpy.context.object

for layer in range(layers_count):
    z_position = layer * layer_thickness
    rotation_angle = layer * angle_per_layer

    # Create a parent empty object
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_position))
    empty_object = bpy.context.object

    fiber_diameter = layer_thickness
    number_of_fibers = max(1, int(plate_dimension / fiber_diameter))
    spacing = plate_dimension - (number_of_fibers * fiber_diameter)
    start_y = -plate_dimension / 2 + (fiber_diameter / 2) + (spacing / 2)

    for i in range(number_of_fibers):
        fiber_y = start_y + i * fiber_diameter
        fiber_instance = create_fiber(fiber_type, fiber_diameter, 0, fiber_y, z_position)
        fiber_instance.parent = empty_object
        fiber_instance.location = (0, fiber_y, 0)

    bpy.context.view_layer.objects.active = empty_object
    empty_object.select_set(True)
    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')
