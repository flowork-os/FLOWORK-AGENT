# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script_create_a_model_of_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script create a model of a tubular bioinspired structure

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the number of cylinders
tubule_total = 9

def build_tubule_grid(total):
    # Create a cube and subtract tubules from it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(total))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2
    for i in range(total):
        x = start_offset + (i % grid_dim) * spacing
        y = start_offset + (i // grid_dim) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        bool_mod = main_cube.modifiers.new(name=f"Subtraction_{i}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the creation of the tubule grid
build_tubule_grid(tubule_total)
