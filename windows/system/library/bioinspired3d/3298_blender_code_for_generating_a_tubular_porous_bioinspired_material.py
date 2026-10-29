# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_generating_a_tubular_porous_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for generating a tubular porous bioinspired material.

import bpy
import math

# Clear the current scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the number of tubules
tubule_amount = 20

def create_cuboid_with_tubules():
    # Function to create a cuboid and subtract tubules from it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_amount))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    for i in range(tubule_amount):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        add_and_subtract_tubule(cube_obj, x, y)

def add_and_subtract_tubule(cube, x_pos, y_pos):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
    tubule_obj = bpy.context.object
    
    bool_mod = cube.modifiers.new(name='Boolean', type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = tubule_obj
    
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(tubule_obj, do_unlink=True)

# Execute the creation function
create_cuboid_with_tubules()
