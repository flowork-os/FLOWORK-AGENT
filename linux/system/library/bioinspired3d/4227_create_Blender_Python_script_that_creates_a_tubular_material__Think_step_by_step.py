# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_Blender_Python_script_that_creates_a_tubular_material__Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create Blender Python script that creates a tubular material. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

amount_of_tubules = 18
ellipse_factor = 1.1
radius_of_tubules = 0.09

def construct_tubule_grid(amount, ellipse, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(amount))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    for i in range(amount):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        create_and_subtract_tubule(x, y, radius, ellipse, main_cube)

def create_and_subtract_tubule(x, y, radius, ellipse, cube):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    tubule.scale[0] *= ellipse

    bool_modifier = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = tubule

    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

construct_tubule_grid(amount_of_tubules, ellipse_factor, radius_of_tubules)
