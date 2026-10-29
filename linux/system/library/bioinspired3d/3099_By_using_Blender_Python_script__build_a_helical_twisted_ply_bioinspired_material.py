# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script__build_a_helical_twisted_ply_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script, build a helical twisted ply bioinspired material made of cylindrical fibers.

import bpy
import math

# Clear the scene before creation
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define helical structure parameters
ply_count = 6
rotation_degree = 20
fiber_model = 'cylinder'

# Dimensions for the structure
total_structure_height = 2
plate_dimensions = 2
thickness_per_ply = total_structure_height / ply_count

def add_helical_fiber(shape, diameter, loc):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter / 2,
        depth=plate_dimensions,
        location=loc,
        rotation=(0, math.radians(90), 0)
    )
    return bpy.context.object

def create_helical_ply(ply_index):
    z_loc = ply_index * thickness_per_ply
    rotation_angle = ply_index * rotation_degree

    # Create a parent empty object
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, z_loc))
    empty_ply = bpy.context.object

    fiber_diameter = thickness_per_ply
    fiber_quantity = max(1, int(plate_dimensions / fiber_diameter))

    total_fiber_space = fiber_quantity * fiber_diameter
    leftover_space = plate_dimensions - total_fiber_space
    start_y_loc = -plate_dimensions / 2 + (fiber_diameter / 2) + (leftover_space / 2)

    for i in range(fiber_quantity):
        fiber_y_loc = start_y_loc + i * fiber_diameter
        fiber_obj = add_helical_fiber(fiber_model, fiber_diameter, (0, fiber_y_loc, z_loc))
        fiber_obj.parent = empty_ply
        fiber_obj.location = (0, fiber_y_loc, 0)

    # Rotate the empty object to create the helical effect
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = empty_ply
    empty_ply.select_set(True)

    bpy.ops.transform.rotate(value=math.radians(rotation_angle), orient_axis='Z')

# Build the helical structure
for index in range(ply_count):
    create_helical_ply(index)
