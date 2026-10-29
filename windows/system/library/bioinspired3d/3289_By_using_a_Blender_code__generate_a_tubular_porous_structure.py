# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code__generate_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code, generate a tubular porous structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of tubular structures
count_of_tubules = 12

def generate_tubular_structure(count):
    cube = create_base_cube()
    layout_tubules(cube, count)

def create_base_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.object

def layout_tubules(cube, count):
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    for i in range(count):
        x = offset + (i % grid_dim) * spacing
        y = offset + (i // grid_dim) * spacing
        add_and_subtract_tubule(cube, x, y)

def add_and_subtract_tubule(cube, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    boolean_modifier = cube.modifiers.new(name=f'Cutout_{x}_{y}', type='BOOLEAN')
    boolean_modifier.operation = 'DIFFERENCE'
    boolean_modifier.object = tubule
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

# Start the generation process
generate_tubular_structure(count_of_tubules)
