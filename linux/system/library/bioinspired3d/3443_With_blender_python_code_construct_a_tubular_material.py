# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_python_code_construct_a_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender python code construct a tubular material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters for the structure
count_of_tubules = 12  # Number of tubules
ellipse_factor = 1.8  # Ellipticity
radius_of_tube = 0.1  # Radius for the tubules

def generate_tubule_structure(count, ellipse=1.0, radius=0.1):
    # Function to create a cube with a grid of tubules.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_shape = bpy.context.object
    grid_count = math.ceil(math.sqrt(count))
    spacing_distance = 2 / grid_count
    start_position = -1 + spacing_distance / 2
    tubule_positions = [(start_position + (i % grid_count) * spacing_distance, 
                         start_position + (i // grid_count) * spacing_distance) 
                        for i in range(count)]
    for pos_x, pos_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        tube = bpy.context.object
        tube.scale[0] *= ellipse
        boolean_op = cube_shape.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        boolean_op.operation = 'DIFFERENCE'
        boolean_op.object = tube
        bpy.context.view_layer.objects.active = cube_shape
        bpy.ops.object.modifier_apply(modifier=boolean_op.name)
        bpy.data.objects.remove(tube, do_unlink=True)

# Create the tubular structure
generate_tubule_structure(count_of_tubules, ellipse_factor, radius_of_tube)
