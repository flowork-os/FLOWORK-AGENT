# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_a_tubular_structure_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of a tubular structure in a blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_of_tubules = 10
elliptical_factor = 1.4
radius_of_tubules = 0.05

def construct_tubule_cube(num_of_tubules, elliptical_factor=1.0, radius_of_tubules=0.1):
    # This function creates a 3D model by subtracting tubules from a cube.
    # Process:
    # 1. Create a cube as the base.
    # 2. Define positions for the tubules.
    # 3. Utilize Boolean modifiers for subtraction.
    
    # Create the initial cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    # Determine the grid size
    grid_size = math.ceil(math.sqrt(num_of_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Generate positions for the tubules
    positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(num_of_tubules)]
    
    # Subtract tubules from the cube
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_tubules, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= elliptical_factor
        
        # Create and apply Boolean modifier
        boolean_mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        
        # Clean up the tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the tubular structure
construct_tubule_cube(num_of_tubules, elliptical_factor, radius_of_tubules)
