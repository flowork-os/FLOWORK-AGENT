# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_Blender_code_that_generates_a_cube_of_tubular_bioinspired_material__Think_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make Blender code that generates a cube of tubular bioinspired material. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular assembly
num_tubules = 20
stretch_ratio = 1.7
base_tubule_radius = 0.07

class TubuleCreator:
    @staticmethod
    def build_tubule_structure(count, stretch=1.0, radius=0.1):
        # Constructs a cube and subtracts a grid of tubules from it.
        # Steps:
        # 1. Create a cube.
        # 2. Calculate positions for tubules.
        # 3. Use Boolean modifiers.
        
        # Create the base cube
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.object
        
        # Determine grid size
        grid_size = math.ceil(math.sqrt(count))
        spacing = 2 / grid_size
        offset = -1 + spacing / 2
        
        # Generate positions for tubules
        positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(count)]
        
        # Iterate through positions to create tubules
        for x, y in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
            tubule = bpy.context.object
            tubule.scale[0] *= stretch
            
            # Create Boolean modifier to subtract the tubule from the cube
            mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = tubule
            
            bpy.context.view_layer.objects.active = cube
            bpy.ops.object.modifier_apply(modifier=mod.name)
            
            # Clean up the tubule object
            bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the creation of the tubular structure
TubuleCreator.build_tubule_structure(num_tubules, stretch_ratio, base_tubule_radius)
