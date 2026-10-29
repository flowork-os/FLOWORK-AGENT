# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_build_a_tubular_bioinspired_structure__think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to build a tubular bioinspired structure. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_of_tubules = 12
ellipse_scale = 1.6
radius_of_tube = 0.07

def create_cuboidal_tubules(num_tubules, ellipse, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_dim
    start = -1 + spacing / 2

    positions = [(start + (i % grid_dim) * spacing, start + (i // grid_dim) * spacing) for i in range(num_tubules)]

    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipse

        bool_mod = cube.modifiers.new(name=f'Boolean_{x}_{y}', type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(tubule, do_unlink=True)

create_cuboidal_tubules(num_of_tubules, ellipse_scale, radius_of_tube)
