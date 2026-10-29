# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_a_cube_of_tubular_bioinspired_material_using_Blender_code_th" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of a cube of tubular bioinspired material using Blender code think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular model
num_tubes = 20
stretch_ratio = 1.1
tube_radius = 0.08

def construct_tubule_cube(tube_count, stretch=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object

    grid_dim = math.ceil(math.sqrt(tube_count))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2

    positions = [(start_offset + (i % grid_dim) * spacing,
                  start_offset + (i // grid_dim) * spacing)
                 for i in range(tube_count)]

    for position in positions:
        x, y = position
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tube = bpy.context.object
        tube.scale[0] *= stretch

        bool_modifier = base_cube.modifiers.new(name=f"Subtraction_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tube

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(tube, do_unlink=True)

construct_tubule_cube(num_tubes, stretch_ratio, tube_radius)
