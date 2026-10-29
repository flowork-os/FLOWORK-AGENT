# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script__generate_a_tubular_bioinspired_structure_think_step_b" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script, generate a tubular bioinspired structure think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubes = 16  # Number of tubules
stretch_factor = 1.5  # Ellipticity factor
base_radius = 0.08  # Radius of the tubules

# Function to create a grid of tubules
def build_tubule_structure(tube_count, stretch=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tube_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(tube_count)]

    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        tube.scale[0] *= stretch
        bool_modifier = main_cube.modifiers.new(name=f"Subtraction_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tube, do_unlink=True)

# Execute structure creation
build_tubule_structure(num_tubes, stretch_factor, base_radius)
