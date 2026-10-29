# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_python_code__construct_a_model_of_a_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender python code, construct a model of a tubular material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of cylindrical features in the design
num_tubules = 16

# Function to construct the grid of cylinders

def build_tubule_grid():
    # Step-by-step process to create the tubule structure
    # 1. Start with a cube.
    # 2. Calculate positions for each tubule.
    # 3. Use Boolean operations to subtract the tubules from the cube.
    
    base_cube = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(num_tubules))
    offset = 2 / grid_dim
    initial_offset = -1 + offset / 2
    
    tubule_positions = [
        (initial_offset + (i % grid_dim) * offset,
         initial_offset + (i // grid_dim) * offset)
        for i in range(num_tubules)
    ]
    
    for x, y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule_cylinder = bpy.context.object
        
        boolean_mod = cube_obj.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule_cylinder
        
        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        
        bpy.data.objects.remove(tubule_cylinder, do_unlink=True)

# Execute the tubule creation
build_tubule_grid()
