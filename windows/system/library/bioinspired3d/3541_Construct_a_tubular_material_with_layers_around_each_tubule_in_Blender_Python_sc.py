# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_tubular_material_with_layers_around_each_tubule_in_Blender_Python_sc" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a tubular material with layers around each tubule in Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular framework
num_tubules = 10  # Total number of tubules
layer_thickness = 0.07  # Thickness of the layer around each tubule

def create_tubular_shape():
    # Function to build a cube and arrange tubules within it.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    positions = [(offset + (i % grid_size) * spacing,
                  offset + (i // grid_size) * spacing)
                 for i in range(num_tubules)]

    tubular_layers = []

    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tubule = bpy.context.object

        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_tubule = bpy.context.object

        bool_mod = cube.modifiers.new(name="Cube_Bool", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        layer_mod = inner_tubule.modifiers.new(name="Layer_Bool", type='BOOLEAN')
        layer_mod.operation = 'DIFFERENCE'
        layer_mod.object = outer_tubule
        bpy.context.view_layer.objects.active = inner_tubule
        bpy.ops.object.modifier_apply(modifier=layer_mod.name)

        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        tubular_layers.append(inner_tubule)

    if tubular_layers:
        bpy.ops.object.select_all(action='DESELECT')
        for layer in tubular_layers:
            layer.select_set(True)
        bpy.context.view_layer.objects.active = tubular_layers[0]
        bpy.ops.object.join()
        final_shape = bpy.context.object
        final_shape.name = "Tubular_Shape"

# Create the tubular shape
create_tubular_shape()
