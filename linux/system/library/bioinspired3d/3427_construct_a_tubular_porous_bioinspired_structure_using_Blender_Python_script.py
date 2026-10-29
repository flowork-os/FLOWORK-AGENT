# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_tubular_porous_bioinspired_structure_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a tubular porous bioinspired structure using Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular grid
total_tubules = 12  # Number of tubules
ellipse_factor = 1.2  # Stretch factor for tubules
radius_size = 0.06  # Radius of each tubule


def create_tubules_in_cube(count, ellipticity=1.0, radius=0.1):
    # Create a cube and subtract tubules from it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(count))
    gap = 2 / grid_dimension
    initial_position = -1 + gap / 2
    
    coords = [(initial_position + (i % grid_dimension) * gap, initial_position + (i // grid_dimension) * gap) for i in range(count)]
    
    for pos_x, pos_y in coords:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        
        bool_mod = cube_object.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the creation of the structure
create_tubules_in_cube(total_tubules, ellipse_factor, radius_size)
