# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_python_code_that_builds_a_tubular_porous_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender python code that builds a tubular porous material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule construction parameters
num_tubules = 10  # Number of tubules
ellipticity_factor = 1.6  # Stretch factor
base_radius = 0.09  # Radius of the tubules

def create_tubule_structure(tubule_count, ellipticity, radius):
    # This function creates a cube and subtracts tubules from it.
    # 1. Create a cube.
    # 2. Calculate positions for tubules.
    # 3. Subtract using Boolean modifiers.
    
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    
    # Calculate grid size
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Calculate positions for tubules
    positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(tubule_count)]
    
    # Subtract each tubule from the cube
    for position in positions:
        x, y = position
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity  # Apply ellipticity
        
        # Create and apply Boolean modifier
        bool_mod = cube_base.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        # Apply the modifier
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Remove the tubule from the scene
        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the tubular structure
create_tubule_structure(num_tubules, ellipticity_factor, base_radius)
