# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_making_a_model_of_a_tubular_porous_structure_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for making a model of a tubular porous structure with layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters
num_tubules = 12  # Total number of tubules
layer_thickness_value = 0.04  # Thickness of the layer surrounding each tubule

def build_tubule_structure():
    # Create a cube and position tubules
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    dimension = math.ceil(math.sqrt(num_tubules))
    interval = 2 / dimension
    start = -1 + interval / 2
    coords = [(start + (i % dimension) * interval, start + (i // dimension) * interval) for i in range(num_tubules)]
    tubule_layers = []
    for x, y in coords:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        bool_mod = cube_base.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tubule
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bool_mod_outer = inner_tubule.modifiers.new(name=f"Outer_Bool_{x}_{y}", type='BOOLEAN')
        bool_mod_outer.operation = 'DIFFERENCE'
        bool_mod_outer.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=bool_mod_outer.name)
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        tubule_layers.append(inner_tubule)
    if tubule_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in tubule_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = tubule_layers[0]
        bpy.ops.object.join()
        final_tubule_shell = bpy.context.object
        final_tubule_shell.name = "Final_Tubule_Shell"

build_tubule_structure()
