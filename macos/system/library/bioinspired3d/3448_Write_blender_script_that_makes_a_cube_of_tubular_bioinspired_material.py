# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_that_makes_a_cube_of_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script that makes a cube of tubular bioinspired material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule definition parameters
num_tubules = 20  # Total number of tubules
stretch_ratio = 1.8  # Ellipticity factor
base_tubule_radius = 0.07  # Radius of tubules

def generate_tubule_cube(tubule_count, stretch, radius):
    # Constructs a cube and subtracts tubules from it.
    # Steps:
    # 1. Create a cube.
    # 2. Calculate positions for tubules.
    # 3. Subtract using Boolean operations.
    
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    # Calculate grid layout
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dim
    start_pos = -1 + spacing / 2
    
    # Determine tubule positions
    positions = [(start_pos + (i % grid_dim) * spacing, start_pos + (i // grid_dim) * spacing) for i in range(tubule_count)]
    
    # Create and subtract each tubule
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= stretch  # Apply stretch ratio
        
        # Create Boolean modifier for subtraction
        mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = tubule
        
        # Apply the modifier
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=mod.name)
        
        # Remove the tubule from the scene
        bpy.data.objects.remove(tubule, do_unlink=True)

# Call the function to create the tubular structure
generate_tubule_cube(num_tubules, stretch_ratio, base_tubule_radius)
