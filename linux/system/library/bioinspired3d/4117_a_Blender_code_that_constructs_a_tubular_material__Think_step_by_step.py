# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_constructs_a_tubular_material__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that constructs a tubular material. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the total number of tubes
tube_count = 25

def build_tubes():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    arrange_tubes(main_cube)

def arrange_tubes(cube):
    grid_dimension = math.ceil(math.sqrt(tube_count))
    distance = 2 / grid_dimension
    initial_offset = -1 + distance / 2

    for index in range(tube_count):
        x_pos = initial_offset + (index % grid_dimension) * distance
        y_pos = initial_offset + (index // grid_dimension) * distance
        create_and_subtract_tube(cube, x_pos, y_pos)

def create_and_subtract_tube(cube, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tube = bpy.context.object
    bool_modifier = cube.modifiers.new(name=f'Cutout_{x}_{y}', type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = tube
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
    bpy.data.objects.remove(tube, do_unlink=True)

# Execute the tube building process
build_tubes()
