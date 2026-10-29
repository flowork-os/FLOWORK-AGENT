# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_building_a_tubular_porous_bioinspired_structure_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for building a tubular porous bioinspired structure with layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Constants for the design
num_tubules = 20  # Total number of tubules
layer_thickness = 0.04  # Thickness of the layer

# Function to generate the entire structure
def generate_tubule_structure():
    # Step 1: Create a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object

    # Step 2: Calculate grid dimensions
    grid_dim = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_dim
    start_pos = -1 + spacing / 2

    # Step 3: Create positions for tubules
    tubule_locations = [(start_pos + (i % grid_dim) * spacing,
                         start_pos + (i // grid_dim) * spacing)
                        for i in range(num_tubules)]

    # Step 4: Prepare to store tubule layers
    layer_objects = []

    # Step 5: Create tubules in the grid
    for pos_x, pos_y in tubule_locations:
        inner_tube = create_inner_tubule(pos_x, pos_y)
        outer_tube = create_outer_tubule(pos_x, pos_y)

        # Apply Boolean operations
        apply_boolean(cube, inner_tube)
        apply_boolean(inner_tube, outer_tube)
        
        # Clean up the outer tube
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        layer_objects.append(inner_tube)

    # Step 6: Merge all layers into one object
    if layer_objects:
        merge_layers(layer_objects)

def create_inner_tubule(x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
    return bpy.context.object

def create_outer_tubule(x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
    return bpy.context.object

def apply_boolean(target, source):
    modifier = target.modifiers.new(name="Boolean_Modifier", type='BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.object = source
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=modifier.name)

def merge_layers(layers):
    bpy.ops.object.select_all(action='DESELECT')
    for layer in layers:
        layer.select_set(True)
    bpy.context.view_layer.objects.active = layers[0]
    bpy.ops.object.join()
    final_object = bpy.context.object
    final_object.name = "Final_Tubule_Structure"

# Execute the structure generation
generate_tubule_structure()
