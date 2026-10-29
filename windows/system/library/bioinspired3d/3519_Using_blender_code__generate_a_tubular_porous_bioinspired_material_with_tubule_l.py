# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_code__generate_a_tubular_porous_bioinspired_material_with_tubule_l" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender code, generate a tubular porous bioinspired material with tubule layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 16  # Number of tubules in the structure
layer_width = 0.05  # Thickness of the layer surrounding each tubule

def build_tubule_structure():
    # Function to create a cube with a grid of tubules surrounded by a layer.
    # Steps:
    # 1. Create a base cube.
    # 2. Arrange tubules in a grid.
    # 3. Create inner and outer tubules for each grid position.
    # 4. Use Boolean modifiers to subtract inner tubules from the cube.
    # 5. Use Boolean modifiers to subtract inner tubules from outer tubules to create layers.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(total_tubules))
    gap = 2 / grid_dim
    offset = -1 + gap / 2
    positions = [(offset + (i % grid_dim) * gap, offset + (i // grid_dim) * gap) for i in range(total_tubules)]
    shells = []
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        bool_mod = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        layer_mod = inner_tube.modifiers.new(name=f"LayerBool_{x}_{y}", type='BOOLEAN')
        layer_mod.operation = 'DIFFERENCE'
        layer_mod.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_mod.name)
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        shells.append(inner_tube)
    
    if shells:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in shells:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = shells[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Shell"

build_tubule_structure()
