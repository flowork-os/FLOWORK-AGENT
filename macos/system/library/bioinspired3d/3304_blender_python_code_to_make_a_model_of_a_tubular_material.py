# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_make_a_model_of_a_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to make a model of a tubular material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the number of tubules
number_of_tubules = 20

def build_tubule_structure():
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_size = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_size
    start = -1 + spacing / 2

    # Generate positions for each tubule
    for i in range(number_of_tubules):
        x_coord = start + (i % grid_size) * spacing
        y_coord = start + (i // grid_size) * spacing
        create_and_subtract_tubule(cube_object, x_coord, y_coord)


def create_and_subtract_tubule(cube, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    boolean_mod = cube.modifiers.new(name='TubuleBoolean', type='BOOLEAN')
    boolean_mod.operation = 'DIFFERENCE'
    boolean_mod.object = tubule
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

# Build the tubular structure
build_tubule_structure()
