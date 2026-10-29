# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender__generate_a_model_of_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender, generate a model of a tubular porous structure.

import bpy
import math

# Clear the current Blender scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the total number of tubules
tubule_total = 9

def build_tubule_structure(total):
    # Create a base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object

    # Compute grid dimensions
    grid_dim = math.ceil(math.sqrt(total))
    spacing = 2 / grid_dim
    start_pos = -1 + spacing / 2

    # Generate positions for each tubule
    positions = [(start_pos + (i % grid_dim) * spacing,
                  start_pos + (i // grid_dim) * spacing)
                 for i in range(total)]

    # Create and subtract tubules from the cube
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object

        boolean_modifier = base_cube.modifiers.new(name=f"Subtraction_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the function to build the structure
build_tubule_structure(tubule_total)
