# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_python_code__construct_a_model_of_a_tubular_porous_bioinspired_mate" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender python code, construct a model of a tubular porous bioinspired material.

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the number of tubules
num_of_tubules = 9

def construct_tubule_cube():
    # This function creates a cube with a grid of tubules.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_of_tubules))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    for i in range(num_of_tubules):
        x = start_offset + (i % grid_size) * spacing
        y = start_offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        cylinder = bpy.context.object
        boolean_modifier = cube.modifiers.new(name=f"Subtract_{i}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = cylinder
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

# Create the tubule structure
construct_tubule_cube()
