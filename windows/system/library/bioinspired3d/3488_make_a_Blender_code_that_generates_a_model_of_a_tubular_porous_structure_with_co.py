# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_Blender_code_that_generates_a_model_of_a_tubular_porous_structure_with_co" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a Blender code that generates a model of a tubular porous structure with cortical layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the model
num_tubules = 12  # Total number of tubules
layer_thickness = 0.06  # Thickness of the layer surrounding each tubule

# Main function to create the structure
def build_tubule_structure():
    # Add a base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid layout
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    # List to hold tubule positions
    tubule_positions = [(offset + (i % grid_size) * spacing,
                         offset + (i // grid_size) * spacing)
                        for i in range(num_tubules)]

    # List for storing created tubule layers
    created_layers = []

    # Create tubules in the grid
    for pos_x, pos_y in tubule_positions:
        inner_tube = create_inner_tubule(pos_x, pos_y)
        outer_tube = create_outer_tubule(pos_x, pos_y)
        
        # Subtract inner tube from cube
        apply_boolean(base_cube, inner_tube)
        # Subtract outer tube from inner tube
        apply_boolean(inner_tube, outer_tube)
        
        # Clean up the outer tube
        bpy.data.objects.remove(outer_tube, do_unlink=True)
        created_layers.append(inner_tube)

    # Merge all created layers into one object
    if created_layers:
        join_layers(created_layers)

def create_inner_tubule(x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
    return bpy.context.object

def create_outer_tubule(x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
    return bpy.context.object

def apply_boolean(target, source):
    mod = target.modifiers.new(name='Boolean', type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = source
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)

def join_layers(layers):
    bpy.ops.object.select_all(action='DESELECT')
    for layer in layers:
        layer.select_set(True)
    bpy.context.view_layer.objects.active = layers[0]
    bpy.ops.object.join()
    final_object = bpy.context.object
    final_object.name = "Tubule_Structure"

# Build the tubule structure
build_tubule_structure()
