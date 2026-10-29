# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_python_blender_code_construct_a_model_of_a_tubular_structure_with_tubule_la" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with python blender code construct a model of a tubular structure with tubule layers. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the structure
num_tubules = 25  # Total number of tubules
layer_thickness = 0.06  # Thickness around each tubule

def construct_tubules():
    # Function to create a grid of tubules surrounded by a layer within a cube.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    tubule_positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(num_tubules)]
    layers = []
    for pos in tubule_positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object
        cube.modifiers.new(name=f"Cube_Bool_{x}_{y}", type='BOOLEAN')
        cube.modifiers[-1].operation = 'DIFFERENCE'
        cube.modifiers[-1].object = inner_tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=cube.modifiers[-1].name)
        inner_tubule.modifiers.new(name=f"Inner_Bool_{x}_{y}", type='BOOLEAN')
        inner_tubule.modifiers[-1].operation = 'DIFFERENCE'
        inner_tubule.modifiers[-1].object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=inner_tubule.modifiers[-1].name)
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        layers.append(inner_tubule)
    if layers:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layers:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layers[0]
        bpy.ops.object.join()
        complete_structure = bpy.context.object
        complete_structure.name = "Complete_Tubule_Structure"

# Execute the construction
construct_tubules()
