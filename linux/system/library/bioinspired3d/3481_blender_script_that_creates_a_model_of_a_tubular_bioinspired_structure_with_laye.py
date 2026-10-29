# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_creates_a_model_of_a_tubular_bioinspired_structure_with_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that creates a model of a tubular bioinspired structure with layers around each tubule

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular formation
num_tubules = 16  # Total number of tubules in the structure
layer_width = 0.04  # Thickness of layer surrounding each tubule

def build_tubules():
    # Constructs a cube with a grid of tubules surrounded by a layer.
    # Steps:
    # 1. Creates a cube.
    # 2. Positions tubules in a grid layout.
    # 3. Generates inner and outer tubules for each grid point.
    # 4. Applies Boolean modifiers to subtract inner tubules from the cube.
    # 5. Applies Boolean modifiers to subtract inner tubule from outer tubule to create a layer.

    # Create a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    # Calculate grid layout for tubules
    grid_dim = math.ceil(math.sqrt(num_tubules))
    gap = 2 / grid_dim
    start_point = -1 + gap / 2
    
    # Calculate positions for tubules in the grid
    tubule_positions = [(start_point + (i % grid_dim) * gap, 
                         start_point + (i // grid_dim) * gap) 
                        for i in range(num_tubules)]
    
    # List to hold layer objects for merging
    shell_objects = []
    
    # Create and subtract tubules from the cube
    for x, y in tubule_positions:
        # Create an inner cylinder (tubule)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_tube = bpy.context.object

        # Create an outer layer at the same position
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_width, depth=2, location=(x, y, 0))
        outer_tube = bpy.context.object
        
        # Boolean modifier to subtract inner tube from the cube
        bool_mod = base_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_tube
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Boolean modifier to subtract outer tube from inner tube
        shell_mod = inner_tube.modifiers.new(name=f"Shell_{x}_{y}", type='BOOLEAN')
        shell_mod.operation = 'DIFFERENCE'
        shell_mod.object = outer_tube
        bpy.context.view_layer.objects.active = inner_tube
        bpy.ops.object.modifier_apply(modifier=shell_mod.name)

        # Remove the outer tube object after processing
        bpy.data.objects.remove(outer_tube, do_unlink=True)

        # Store the processed inner tube for merging
        shell_objects.append(inner_tube)
        
    # Merge all shell objects into one
    if shell_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in shell_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = shell_objects[0]
        bpy.ops.object.join()
        final_shell = bpy.context.object
        final_shell.name = "Final_Shell"

# Create the tubular structure with layers
build_tubules()
