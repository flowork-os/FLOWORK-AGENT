# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_python_blender_code_that_makes_a_tubular_porous_bioinspired_structure__Thin" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make python blender code that makes a tubular porous bioinspired structure. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_of_tubules = 10
elliptical_factor = 1.4
radius_of_tubules = 0.05

def construct_tubule_cube(num_of_tubules, elliptical_factor=1.0, radius_of_tubules=0.1):
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
