# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_construct_a_model_of_a_tubular_bioinspired_material_Thi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to construct a model of a tubular bioinspired material Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Total number of tubules
stretch_factor = 1.5  # Factor to stretch tubules into ellipses
base_radius = 0.08  # Base radius of the tubules

def build_tubule_structure(tubule_count, ellipticity=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(tubule_count)]
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        modifier = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

build_tubule_structure(num_tubules, stretch_factor, base_radius)
