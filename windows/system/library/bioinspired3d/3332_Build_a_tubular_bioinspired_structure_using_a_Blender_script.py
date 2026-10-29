# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_tubular_bioinspired_structure_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a tubular bioinspired structure using a Blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set the number of tubular sections
number_of_tubules = 25

def create_cuboid_with_tubules():
    # This function constructs a cube with cylindrical voids.
    # The process involves:
    # 1. Adding a base cube.
    # 2. Calculating cylinder placements.
    # 3. Applying Boolean modifiers to subtract cylinders.
    
    # Start with a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_object = bpy.context.object
    
    # Grid calculations
    grid_size = math.ceil(math.sqrt(number_of_tubules))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    # Position calculations for the cylinders
    positions = [(offset + (i % grid_size) * spacing,
                  offset + (i // grid_size) * spacing)
                 for i in range(number_of_tubules)]
    
    # Create and subtract cylinders
    for pos in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos[0], pos[1], 0))
        cylinder = bpy.context.object

        boolean_mod = base_object.modifiers.new(name=f"Remove_{pos[0]}_{pos[1]}", type='BOOLEAN')
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.object = cylinder

        bpy.context.view_layer.objects.active = base_object
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        bpy.data.objects.remove(cylinder, do_unlink=True)

# Execute the creation function
create_cuboid_with_tubules()
