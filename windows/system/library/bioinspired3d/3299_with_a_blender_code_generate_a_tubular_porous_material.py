# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_blender_code_generate_a_tubular_porous_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a blender code generate a tubular porous material.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubules
num_tubules = 12

def create_structure():
    # This function builds a structure with a cube and several tubules
    cube = create_cube()
    positions = calculate_positions(num_tubules)
    for pos in positions:
        create_and_subtract_tubule(cube, pos)

def create_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.object

def calculate_positions(count):
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    return [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(count)]

def create_and_subtract_tubule(cube, position):
    x, y = position
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    bool_mod = cube.modifiers.new(name='Subtract', type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = tubule
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

# Run the structure creation
create_structure()
