# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_making_a_tubular_material_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for making a tubular material with layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
num_tubules = 25  # Number of tubules to create
thickness = 0.04  # Thickness of each layer

def create_structure():
    # This function builds a cube with multiple tubules arranged in a grid.
    # Process:
    # 1. Construct a cube.
    # 2. Place tubules in a grid layout.
    # 3. Create inner and outer tubules for each grid cell.
    # 4. Apply Boolean modifiers to subtract inner tubules from the cube.
    # 5. Subtract outer from inner tubules to form layers.

    cube = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start = -1 + spacing / 2

    tubule_positions = [(start + (i % grid_size) * spacing, 
                         start + (i // grid_size) * spacing) 
                        for i in range(num_tubules)]

    created_layers = []

    for pos in tubule_positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - thickness, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object

        cube_mod = base_cube.modifiers.new(name="Subtract_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        cube_mod.operation = 'DIFFERENCE'
        cube_mod.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=cube_mod.name)

        layer_mod = inner_tube.modifiers.new(name="Layer_{:.2f}_{:.2f}".format(x, y), type='BOOLEAN')
        layer_mod.operation = 'DIFFERENCE'
        layer_mod.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_mod.name)

        bpy.data.objects.remove(outer_tube, do_unlink=True)
        created_layers.append(inner_tube)

    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in created_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        final_object = bpy.context.object
        final_object.name = "Tubular_Structure"

# Invoke the structure creation function
create_structure()
