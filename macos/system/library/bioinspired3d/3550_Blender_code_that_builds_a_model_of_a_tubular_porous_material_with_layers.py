# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_builds_a_model_of_a_tubular_porous_material_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that builds a model of a tubular porous material with layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular framework
num_tubules = 16  # Total number of tubes in the structure
layer_thickness = 0.05  # Thickness of the layer around each tube

# Function to construct the tubular structure

def build_tubular_structure():
    # This function constructs a cubic framework with tubular elements.
    # Steps:
    # 1. Create a cube.
    # 2. Arrange tubes in a grid layout.
    # 3. Generate inner and outer tubes for each grid position.
    # 4. Use Boolean modifiers to create the desired geometry.

    # Create the main cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object

    # Determine grid size
    grid_dim = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    # Calculate positions for the tubes
    tube_positions = [(offset + (i % grid_dim) * spacing,
                       offset + (i // grid_dim) * spacing)
                      for i in range(num_tubules)]

    # Store created tube layers
    created_layers = []

    # Process each tube position
    for x, y in tube_positions:
        # Create inner tube
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        # Create outer tube
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object

        # Boolean operation to subtract inner tube from cube
        bool_modifier = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        # Boolean operation to create the shell around the tube
        shell_modifier = inner_tube.modifiers.new(name=f"Shell_{x}_{y}", type='BOOLEAN')
        shell_modifier.operation = 'DIFFERENCE'
        shell_modifier.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=shell_modifier.name)

        # Clean up outer tube
        bpy.data.objects.remove(outer_tube, do_unlink=True)

        # Add inner tube to layers list
        created_layers.append(inner_tube)

    # Combine all inner tubes into a single object
    if created_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in created_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = created_layers[0]
        bpy.ops.object.join()
        final_structure = bpy.context.object
        final_structure.name = "Tubular_Structure"

# Execute tubular structure creation
build_tubular_structure()
