# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_python_blender_code_that_makes_a_model_of_a_cube_of_tubular_material_think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make python blender code that makes a model of a cube of tubular material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 12

def build_tubular_cube():
    cube = create_cube()
    tubule_positions = calculate_positions(total_tubules)
    subtract_tubules(cube, tubule_positions)

def create_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.object

def calculate_positions(count):
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    return [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(count)]

def subtract_tubules(cube, positions):
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object

        bool_mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

build_tubular_cube()
