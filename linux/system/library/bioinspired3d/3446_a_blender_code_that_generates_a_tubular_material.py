# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_generates_a_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that generates a tubular material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the structure of the tubules
num_tubules = 16  # Total number of tubules
stretch_factor = 1.5  # Factor to stretch tubules into ellipses
base_radius = 0.08  # Base radius of the tubules

def build_tubule_structure(total_tubules, stretch=1.0, radius=0.1):
    # This function constructs a cube with a grid of tubules.
    # Steps:
    # 1. Create a cube.
    # 2. Position tubules in a grid.
    # 3. Subtract tubules using Boolean modifiers.
    
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    
    # Determine grid size and spacing
    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    # Calculate positions for each tubule
    coordinates = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(total_tubules)]
    
    # Subtract tubules from the cube
    for coord in coordinates:
        x, y = coord
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule_obj = bpy.context.object
        tubule_obj.scale[0] *= stretch  # Apply stretch factor
        
        # Create a Boolean modifier for subtraction
        bool_modifier = cube_obj.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_obj
        
        # Apply the modifier
        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Remove the tubule object
        bpy.data.objects.remove(tubule_obj, do_unlink=True)

# Build the tubular structure
build_tubule_structure(num_tubules, stretch_factor, base_radius)
