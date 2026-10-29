# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_blender_code_that_creates_a_model_of_a_tubular_bioinspired_structure_with_r" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make blender code that creates a model of a tubular bioinspired structure with random placement.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def create_and_subtract_tubules(tubule_count=25, noise=0.05):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_pos = -1 + spacing / 2

    for i in range(tubule_count):
        x = start_pos + (i % grid_size) * spacing
        y = start_pos + (i // grid_size) * spacing
        x += random.uniform(-noise, noise)
        y += random.uniform(-noise, noise)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        boolean_modifier = cube_object.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

create_and_subtract_tubules(tubule_count=21, noise=0.1)
