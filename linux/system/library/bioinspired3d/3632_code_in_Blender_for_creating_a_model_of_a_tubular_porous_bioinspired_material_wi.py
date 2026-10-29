# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_creating_a_model_of_a_tubular_porous_bioinspired_material_wi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for creating a model of a tubular porous bioinspired material with noise.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule parameters
num_tubes = 25
noise_variation = 0.05

def create_tubular_structure(tubes, noise):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubes))
    spacing = 2 / grid_size
    initial_offset = -1 + spacing / 2

    positions = [(initial_offset + (i % grid_size) * spacing,
                  initial_offset + (i // grid_size) * spacing)
                 for i in range(tubes)]

    for x, y in positions:
        x += random.uniform(-noise, noise)
        y += random.uniform(-noise, noise)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        boolean_modifier = main_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tube, do_unlink=True)

# Execute the creation function
create_tubular_structure(num_tubes, noise_variation)
