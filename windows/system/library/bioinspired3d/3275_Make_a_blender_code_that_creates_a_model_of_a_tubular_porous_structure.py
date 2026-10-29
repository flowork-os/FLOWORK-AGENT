# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_blender_code_that_creates_a_model_of_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a blender code that creates a model of a tubular porous structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubules
tubule_total = 9

def create_structure():
    # Create the main cube and subtract tubules from it
    cube = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    tubule_positions = calculate_tubule_positions(tubule_total)
    for position in tubule_positions:
        add_tubule_and_subtract(cube_object, position)

def calculate_tubule_positions(total):
    grid_size = math.ceil(math.sqrt(total))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    return [(offset + (i % grid_size) * spacing,
             offset + (i // grid_size) * spacing) for i in range(total)]

def add_tubule_and_subtract(cube, position):
    x, y = position
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    bool_modifier = cube.modifiers.new(name=f"Subtraction_{x}_{y}", type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = tubule

    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the structure creation
create_structure()
