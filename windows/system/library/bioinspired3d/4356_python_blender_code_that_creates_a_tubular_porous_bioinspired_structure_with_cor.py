# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_creates_a_tubular_porous_bioinspired_structure_with_cor" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that creates a tubular porous bioinspired structure with cortical layers. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 18  # Number of tubules
layer_thickness = 0.07  # Thickness of the layer

def create_tubule_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(num_tubules)]
    layer_objects = []

    for pos in positions:
        tubule = add_tubule(cube, pos)
        layer_objects.append(tubule)

    merge_layers(layer_objects)

def add_tubule(cube, position):
    x, y = position
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
    inner_tubule = bpy.context.object
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
    outer_tubule = bpy.context.object
    apply_boolean(cube, inner_tubule)
    apply_boolean(inner_tubule, outer_tubule)
    bpy.data.objects.remove(outer_tubule, do_unlink=True)
    return inner_tubule

def apply_boolean(target, obj):
    mod = target.modifiers.new(name="Boolean_Mod", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = obj
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)

def merge_layers(objects):
    if objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Final_Tubule_Structure"

create_tubule_structure()
