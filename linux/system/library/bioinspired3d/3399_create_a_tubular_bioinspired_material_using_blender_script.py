# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_tubular_bioinspired_material_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a tubular bioinspired material using blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular model
total_tubules = 9
stretch_amount = 1.1
tubule_diameter = 0.05

# Function to generate the tubule structure

def generate_tubule_structure(tubule_count, stretch, diameter):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2

    for i in range(tubule_count):
        x = start_offset + (i % grid_size) * spacing
        y = start_offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=diameter, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= stretch
        bool_modifier = main_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Creating the grid of tubules
generate_tubule_structure(total_tubules, stretch_amount, tubule_diameter)
