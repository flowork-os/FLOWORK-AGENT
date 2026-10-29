# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_builds_a_model_of_a_tubular_bioinspired_structure__thin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that builds a model of a tubular bioinspired structure. think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular configuration
num_tubules = 16  # Total number of tubules
stretch_factor = 1.5  # Ellipticity factor
base_radius = 0.08  # Radius of the tubules

def generate_tubule_structure(num_tubules, stretch_factor=1.0, base_radius=0.1):
    # Constructs a cube with a pattern of tubules.
    # Steps:
    # 1. Initialize a cube.
    # 2. Position tubules in a grid.
    # 3. Apply Boolean modifiers for subtraction.
    
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Determine the grid dimensions
    grid_dim = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    # Calculate positions for each tubule
    tubule_positions = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(num_tubules)]
    
    # Create and subtract tubules
    for pos in tubule_positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=base_radius, depth=3, location=(x, y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= stretch_factor
        
        # Add and apply the Boolean modifier
        bool_modifier = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule
        
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Clean up the tubule object
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the tubule generation
generate_tubule_structure(num_tubules, stretch_factor, base_radius)
