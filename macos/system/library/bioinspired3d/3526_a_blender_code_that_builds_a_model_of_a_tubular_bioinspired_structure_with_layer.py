# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_builds_a_model_of_a_tubular_bioinspired_structure_with_layer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that builds a model of a tubular bioinspired structure with layers around each tubule.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
total_tubules = 20  # Total number of tubules
layer_thickness = 0.06  # Layer thickness

def build_tubules():
    # Function to create a cube with a grid of tubules surrounded by a layer.
    # Steps:
    # 1. Create a cube.
    # 2. Position tubules in a grid.
    # 3. Create inner and outer tubules for each grid point.
    # 4. Use Boolean modifiers to subtract inner tubules from the cube.
    # 5. Subtract outer tubules from inner to create layers.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2

    positions = [(start_offset + (i % grid_dim) * spacing, 
                  start_offset + (i // grid_dim) * spacing) 
                 for i in range(total_tubules)]

    layer_objects = []

    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_cylinder = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_cylinder = bpy.context.object

        bool_mod = cube_base.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_cylinder
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        layer_mod = inner_cylinder.modifiers.new(name=f"LayerBool_{x}_{y}", type='BOOLEAN')
        layer_mod.operation = 'DIFFERENCE'
        layer_mod.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=layer_mod.name)

        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        layer_objects.append(inner_cylinder)

    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in layer_objects:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_tubule_shell = bpy.context.object
        final_tubule_shell.name = "Tubule_Shell"

# Build the tubular structure
build_tubules()
