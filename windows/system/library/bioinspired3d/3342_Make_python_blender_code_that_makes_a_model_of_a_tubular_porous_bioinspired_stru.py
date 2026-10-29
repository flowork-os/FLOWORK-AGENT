# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_python_blender_code_that_makes_a_model_of_a_tubular_porous_bioinspired_stru" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make python blender code that makes a model of a tubular porous bioinspired structure

import bpy
import math

# Initialize the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of tubules to create
num_tubules = 12

def build_tubule_structure():
    # Constructs a grid of cylindrical tubules within a cube.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    for i in range(num_tubules):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        boolean_mod = base_cube.modifiers.new(name=f"Cutout_{x}_{y}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = tubule
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the function to create the structure
build_tubule_structure()
