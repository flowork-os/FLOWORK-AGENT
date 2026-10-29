# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_tubular_material_with_layers_around_each_tubule_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a tubular material with layers around each tubule in a Blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure settings
tubule_count = 14  # Total number of tubules
layer_thickness = 0.07  # Thickness of the layer around each tubule

def create_tubular_grid():
    # Builds a cube with a grid of tubules surrounded by a layer.
    # Steps:
    # 1. Generate a cube.
    # 2. Arrange tubules in a grid format.
    # 3. Create inner and outer tubules for each grid coordinate.
    # 4. Apply Boolean modifiers to subtract inner tubules from the cube.
    # 5. Subtract outer tubules from inner tubules to form layers.

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_position = -1 + spacing / 2

    coordinates = [(start_position + (i % grid_size) * spacing, 
                    start_position + (i // grid_size) * spacing) 
                   for i in range(tubule_count)]

    layer_objects = []

    for coord in coordinates:
        x, y = coord
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object

        bool_mod = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        layer_mod = inner_tubule.modifiers.new(name=f"LayerBool_{x}_{y}", type='BOOLEAN')
        layer_mod.operation = 'DIFFERENCE'
        layer_mod.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_mod.name)

        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        layer_objects.append(inner_tubule)

    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in layer_objects:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_tubule_shell = bpy.context.object
        final_tubule_shell.name = "Tubule_Grid"

# Execute the function to create the tubular grid
create_tubular_grid()
