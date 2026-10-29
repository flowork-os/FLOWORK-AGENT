# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_tubular_structure_in_a_Blender_code_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a tubular structure in a Blender code think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 12
stretch_factor = 1.4
tubule_radius = 0.08

def build_tubule_cube(num_tubules, stretch_factor, tubule_radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    for i in range(num_tubules):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        create_tubule(x, y, tubule_radius, stretch_factor, cube)

def create_tubule(x, y, radius, stretch, cube):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    tubule.scale[0] *= stretch

    modifier = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.object = tubule
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

build_tubule_cube(num_tubules, stretch_factor, tubule_radius)
