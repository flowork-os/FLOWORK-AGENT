# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_tubular_bioinspired_structure_with_cortical_layers_using_a_Blender_c" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a tubular bioinspired structure with cortical layers using a Blender code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameter definitions for the tubular structure
num_tubules = 12  # Number of tubules
layer_thickness = 0.03  # Thickness of the surrounding layer

def generate_tubules():
    # Function to create a cube with a grid of tubules surrounded by a layer.
    cube = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(num_tubules)]
    created_layers = []
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        base_cube.modifiers.new(name=f"Sub_{x}_{y}", type='BOOLEAN')
        base_cube.modifiers[-1].operation = 'DIFFERENCE'
        base_cube.modifiers[-1].object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=base_cube.modifiers[-1].name)
        inner_tube.modifiers.new(name=f"Layer_Sub_{x}_{y}", type='BOOLEAN')
        inner_tube.modifiers[-1].operation = 'DIFFERENCE'
        inner_tube.modifiers[-1].object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=inner_tube.modifiers[-1].name)
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        created_layers.append(inner_tube)
    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in created_layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Tubule_Structure"

# Execute tubule generation
generate_tubules()
