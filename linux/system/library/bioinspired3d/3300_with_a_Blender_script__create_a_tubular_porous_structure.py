# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_script__create_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender script, create a tubular porous structure

import bpy
import math

# Clear the existing scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Specify the total number of tubules
total_tubules = 15

def generate_tubular_grid():
    # Function to generate a grid of tubules on a cube
    base_cube = add_cube()
    positions = calculate_grid_positions(total_tubules)
    for pos in positions:
        subtract_tubule(base_cube, pos)

def add_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.object

def calculate_grid_positions(count):
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    return [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(count)]

def subtract_tubule(cube, position):
    x, y = position
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    bool_modifier = cube.modifiers.new(name='Boolean_Subtract', type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = tubule
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the grid generation
generate_tubular_grid()
