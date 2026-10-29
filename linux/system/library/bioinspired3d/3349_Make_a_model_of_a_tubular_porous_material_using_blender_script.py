# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_tubular_porous_material_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a tubular porous material using blender script

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total tubules to create
number_of_tubules = 12

def create_and_subtract_tubules(total_tubules):
    # Step 1: Create a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object

    # Step 2: Calculate grid size and spacing
    grid_size = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_size
    initial_offset = -1 + spacing / 2

    # Step 3: Define positions for each tubule
    positions = [(initial_offset + (i % grid_size) * spacing,
                  initial_offset + (i // grid_size) * spacing)
                 for i in range(total_tubules)]

    # Step 4: Create tubules and apply Boolean modifiers
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule_obj = bpy.context.object

        bool_mod = main_cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule_obj

        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule_obj, do_unlink=True)

# Generate the tubules
create_and_subtract_tubules(number_of_tubules)
