# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_creates_a_tubular_porous_bioinspired_material__Think_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that creates a tubular porous bioinspired material. Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular model
count_tubules = 12
ellipse_scale = 1.1
tubule_diameter = 0.09

def create_tubule_array(count_tubules, ellipse_scale=1.0, tubule_diameter=0.1):
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    # Calculate grid layout
    grid_size = math.ceil(math.sqrt(count_tubules))
    spacing = 2 / grid_size
    start = -1 + spacing / 2
    
    # Calculate positions for the tubules
    positions = [(start + (i % grid_size) * spacing, start + (i // grid_size) * spacing) for i in range(count_tubules)]
    
    # Subtract each tubule from the cube
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=tubule_diameter, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipse_scale
        
        # Create a Boolean modifier
        boolean_mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        
        # Remove the tubule object
        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the tubular array
create_tubule_array(count_tubules, ellipse_scale, tubule_diameter)
