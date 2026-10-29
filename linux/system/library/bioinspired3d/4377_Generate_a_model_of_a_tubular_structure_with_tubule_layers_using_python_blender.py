# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_a_tubular_structure_with_tubule_layers_using_python_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of a tubular structure with tubule layers using python blender code think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Structure parameters
total_tubules = 25  # Number of tubules
layer_width = 0.06  # Layer thickness around tubules

def generate_tubular_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object

    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    positions = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(total_tubules)]

    for pos in positions:
        create_tubule(cube_obj, pos)

def create_tubule(base_cube, position):
    x, y = position
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
    inner_tubule = bpy.context.object

    bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
    outer_tubule = bpy.context.object

    apply_boolean(base_cube, inner_tubule)
    apply_boolean(inner_tubule, outer_tubule)
    bpy.data.objects.remove(outer_tubule, do_unlink=True)

def apply_boolean(target, obj):
    bool_mod = target.modifiers.new(name='BoolMod', type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = obj
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

# Execute the generation
generate_tubular_structure()
