# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_python_code_that_generates_a_model_of_a_tubular_bioinspired_materi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender python code that generates a model of a tubular bioinspired material Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubules = 12
ellipticity_factor = 1.8
base_tubule_radius = 0.06

def generate_tubule_structure(tubule_count, ellipticity=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object

    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_position = -1 + spacing / 2

    tubule_positions = [(start_position + (i % grid_size) * spacing,
                         start_position + (i // grid_size) * spacing)
                        for i in range(tubule_count)]

    for pos in tubule_positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= ellipticity

        boolean_mod = main_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = current_tubule

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        bpy.data.objects.remove(current_tubule, do_unlink=True)

generate_tubule_structure(num_tubules, ellipticity_factor, base_tubule_radius)
