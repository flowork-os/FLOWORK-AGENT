# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_making_a_model_of_a_tubular_porous_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for making a model of a tubular porous bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Specify the number of cylinders to create
num_cylinders = 12  # Total cylinders in the grid

def build_structure():
    """Builds a cube with cylinders removed from it."""
    
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base = bpy.context.object
    
    # Calculate the layout for the cylinders
    grid_size = math.ceil(math.sqrt(num_cylinders))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    
    # Generate positions for the cylinders
    positions = [(start_offset + (i % grid_size) * spacing,
                   start_offset + (i // grid_size) * spacing)
                  for i in range(num_cylinders)]
    
    # Loop to create and subtract cylinders
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(pos_x, pos_y, 0))
        cylinder = bpy.context.object
        bool_modifier = base.modifiers.new(name=f"CutCylinder_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = cylinder
        bpy.context.view_layer.objects.active = base
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

# Execute the build function
build_structure()
