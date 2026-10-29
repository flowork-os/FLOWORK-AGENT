# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_cube_of_tubular_bioinspired_material_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a cube of tubular bioinspired material in blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the total number of tubular elements
total_tubules = 14

def create_tubes():
    # Initialize the main cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dim
    initial_offset = -1 + spacing / 2

    # Loop through and create tubules
    for i in range(total_tubules):
        x_pos = initial_offset + (i % grid_dim) * spacing
        y_pos = initial_offset + (i // grid_dim) * spacing
        subtract_tubule(cube, x_pos, y_pos)


def subtract_tubule(cube, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    boolean_modifier = cube.modifiers.new(name='TubuleModifier', type='BOOLEAN')
    boolean_modifier.operation = 'DIFFERENCE'
    boolean_modifier.object = tubule
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular arrangement
create_tubes()
