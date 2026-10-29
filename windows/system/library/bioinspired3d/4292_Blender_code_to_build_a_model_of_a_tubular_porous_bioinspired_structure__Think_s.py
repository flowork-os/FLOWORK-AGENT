# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_build_a_model_of_a_tubular_porous_bioinspired_structure__Think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to build a model of a tubular porous bioinspired structure. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_tubules = 16  # Total number of tubules
stretch_factor = 1.5  # Factor to stretch tubules into ellipses
base_radius = 0.08  # Base radius of the tubules

def construct_tubular_structure(num_tubules, stretch_factor=1.0, base_radius=0.1):
    # Function to create a cube with a grid of tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(num_tubules)]
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=base_radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= stretch_factor
        bool_mod = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

construct_tubular_structure(num_tubules, stretch_factor, base_radius)
