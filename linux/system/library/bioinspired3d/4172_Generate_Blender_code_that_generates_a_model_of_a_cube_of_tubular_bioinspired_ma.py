# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_code_that_generates_a_model_of_a_cube_of_tubular_bioinspired_ma" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender code that generates a model of a cube of tubular bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 12

def build_tubule_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    for i in range(num_tubules):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        boolean_mod = base_cube.modifiers.new(name=f"Cutout_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

build_tubule_structure()
