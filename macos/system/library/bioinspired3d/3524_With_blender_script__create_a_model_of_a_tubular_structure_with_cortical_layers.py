# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_script__create_a_model_of_a_tubular_structure_with_cortical_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender script, create a model of a tubular structure with cortical layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular configuration
number_of_tubules = 16  # Total number of tubules
layer_width = 0.05  # Width of the layer surrounding each tubule

def generate_tubules():
    # Function to create a cube with a grid of tubules each surrounded by a layer.
    # Steps:
    # 1. Create a cube.
    # 2. Arrange tubules in a grid.
    # 3. Create inner and outer tubules for each grid position.
    # 4. Use Boolean modifiers to subtract inner tubules from the cube.
    # 5. Subtract inner tubules from outer tubules to form layers.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_dimension
    offset = -1 + spacing / 2

    positions = [(offset + (i % grid_dimension) * spacing, 
                  offset + (i // grid_dimension) * spacing) 
                 for i in range(number_of_tubules)]

    layer_objects = []

    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        layer_modifier = inner_tube.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        bpy.data.objects.remove(outer_tube, do_unlink=True)
        layer_objects.append(inner_tube)

    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_layer = bpy.context.object
        final_layer.name = "Tubule_Shell"

# Execute the function to create the tubular structure
generate_tubules()
