# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_code_in_Blender_that_creates_a_tubular_bioinspired_material_with_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make code in Blender that creates a tubular bioinspired material with layers.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the parameters
total_tubules = 21  # Number of tubules in the structure
layer_thickness = 0.07  # Thickness of the surrounding layer

# Function to create the entire structure
def create_structure():
    # Step 1: Create a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Step 2: Set up the grid
    grid_size = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Step 3: Generate tubule positions
    positions = [(start_offset + (i % grid_size) * spacing,
                  start_offset + (i // grid_size) * spacing)
                 for i in range(total_tubules)]

    # Step 4: Prepare to store the tubules
    tubule_layers = []

    # Step 5: Create tubules
    for x, y in positions:
        inner_tubule = create_inner_tubule(x, y)
        outer_tubule = create_outer_tubule(x, y)
        
        # Perform Boolean operations
        apply_boolean(base_cube, inner_tubule)
        apply_boolean(inner_tubule, outer_tubule)
        
        # Clean up the outer tubule
        bpy.data.objects.remove(outer_tubule, do_unlink=True)
        tubule_layers.append(inner_tubule)

    # Step 6: Merge all tubule layers
    if tubule_layers:
        merge_layers(tubule_layers)

def create_inner_tubule(x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
    return bpy.context.object

def create_outer_tubule(x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
    return bpy.context.object

def apply_boolean(target, source):
    modifier = target.modifiers.new(name='Boolean', type='BOOLEAN')
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
    final_object.name = "Final_Tubule_Assembly"

# Run the structure creation function
create_structure()
