# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_code_that_creates_a_model_of_a_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender code that creates a model of a tubular material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
count_tubules = 25
stretch = 1.1
radius_of_tubule = 0.05


def make_tubule_structure(tot_tubules, stretch_factor=1.0, tubule_rad=0.1):
    # Create and configure a cube with tubules subtracted
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    
    grid_count = math.ceil(math.sqrt(tot_tubules))
    gap_between = 2 / grid_count
    initial_offset = -1 + gap_between / 2
    
    positions = [(initial_offset + (i % grid_count) * gap_between, initial_offset + (i // grid_count) * gap_between) for i in range(tot_tubules)]
    
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=tubule_rad, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= stretch_factor
        
        bool_mod = cube_obj.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        bpy.data.objects.remove(tubule, do_unlink=True)

# Build the structure
make_tubule_structure(count_tubules, stretch, radius_of_tubule)
