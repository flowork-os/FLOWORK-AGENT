# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_tubular_porous_bioinspired_material_using_a_blender_code_Think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a tubular porous bioinspired material using a blender code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_of_tubules = 25
ellipse_scale = 1.3
radius_of_tubule = 0.09

def calculate_positions(count):
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    return [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(count)]

def create_tubule_cube(tubule_count, ellipticity, tubule_radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    positions = calculate_positions(tubule_count)

    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=tubule_radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        bool_modifier = cube.modifiers.new(name="Bool_{0}_{1}".format(x, y), type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

create_tubule_cube(num_of_tubules, ellipse_scale, radius_of_tubule)
