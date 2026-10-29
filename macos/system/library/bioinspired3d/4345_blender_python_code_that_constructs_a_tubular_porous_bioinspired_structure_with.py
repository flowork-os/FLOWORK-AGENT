# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_constructs_a_tubular_porous_bioinspired_structure_with" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that constructs a tubular porous bioinspired structure with layers Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 13  # Number of tubules
layer_thickness = 0.06  # Thickness of the layer around each tubule

def build_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    positions = [
        (offset + (i % grid_size) * spacing,
         offset + (i // grid_size) * spacing)
        for i in range(num_tubules)
    ]
    layer_objects = []
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        bool_mod = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        layer_bool_mod = inner_tube.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_bool_mod.operation = 'DIFFERENCE'
        layer_bool_mod.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_bool_mod.name)
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        layer_objects.append(inner_tube)
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Tubule_Grid"

build_tubules()
