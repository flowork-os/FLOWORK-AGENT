# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_python_code_that_constructs_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender python code that constructs a tubular bioinspired structure.

import bpy
import math

# Clear the scene of all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Specify the number of cylinders
num_cylinders = 9

def build_structure():
    # Create the initial cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    # Calculate the layout for cylinders
    grid_length = math.ceil(math.sqrt(num_cylinders))
    spacing_distance = 2 / grid_length
    initial_position = -1 + spacing_distance / 2

    # Generate and position each cylinder
    for index in range(num_cylinders):
        x_coord = initial_position + (index % grid_length) * spacing_distance
        y_coord = initial_position + (index // grid_length) * spacing_distance
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_coord, y_coord, 0))
        cylinder = bpy.context.object

        # Create Boolean modifier to subtract the cylinder
        bool_op = cube_object.modifiers.new(name=f"Remove_{index}", type='BOOLEAN')
        bool_op.operation = 'DIFFERENCE'
        bool_op.object = cylinder

        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_op.name)

        # Delete the cylinder after applying the modifier
        bpy.data.objects.remove(cylinder, do_unlink=True)

# Generate the 3D structure
build_structure()
