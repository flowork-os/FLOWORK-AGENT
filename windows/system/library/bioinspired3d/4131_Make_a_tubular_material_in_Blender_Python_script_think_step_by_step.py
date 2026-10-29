# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_tubular_material_in_Blender_Python_script_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a tubular material in Blender Python script think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of tubes to create
num_tubes = 16

def generate_tube_grid():
    # Function to create a cube with a grid of cylindrical tubes
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(num_tubes))
    spacing = 2 / grid_dimension
    start_position = -1 + spacing / 2

    # Calculate positions for the tubes
    tube_positions = [(start_position + (i % grid_dimension) * spacing,
                       start_position + (i // grid_dimension) * spacing)
                      for i in range(num_tubes)]

    # Create and subtract tubes from the cube
    for pos in tube_positions:
        create_and_subtract_tube(base_cube, pos)

def create_and_subtract_tube(cube, position):
    # Create a tube and subtract it from the cube
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(position[0], position[1], 0))
    tube = bpy.context.object
    bool_mod = cube.modifiers.new(name='Boolean_Tube', type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = tube
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(tube, do_unlink=True)

# Execute the tube grid generation
generate_tube_grid()
