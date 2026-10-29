# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_a_tubular_bioinspired_structure_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of a tubular bioinspired structure in Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of tubules to create
num_tubules = 12

def setup_tubules():
    # Create a cube and subtract tubules from it
    cube = create_base_cube()
    positions = calculate_positions(num_tubules)
    subtract_tubules(cube, positions)

def create_base_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.object

def calculate_positions(count):
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    return [(offset + (i % grid_size) * spacing,
             offset + (i // grid_size) * spacing) for i in range(count)]

def subtract_tubules(cube, positions):
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_modifier = cube.modifiers.new(name=f"Sub_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
setup_tubules()
