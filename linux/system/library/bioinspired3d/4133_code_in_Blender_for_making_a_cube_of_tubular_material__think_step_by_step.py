# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_making_a_cube_of_tubular_material__think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for making a cube of tubular material. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubes
tube_count = 12

# Function to create the cube and subtract tubes
def construct_tube_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(tube_count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    for i in range(tube_count):
        x_pos = offset + (i % grid_dim) * spacing
        y_pos = offset + (i // grid_dim) * spacing
        add_tube_to_cube(main_cube, x_pos, y_pos)

def add_tube_to_cube(cube, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tube = bpy.context.object
    bool_modifier = cube.modifiers.new(name='TubeSubtraction', type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = tube
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
    bpy.data.objects.remove(tube, do_unlink=True)

# Execute the structure creation
construct_tube_structure()
