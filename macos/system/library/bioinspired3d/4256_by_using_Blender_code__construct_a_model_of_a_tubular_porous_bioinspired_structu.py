# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_code__construct_a_model_of_a_tubular_porous_bioinspired_structu" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender code, construct a model of a tubular porous bioinspired structure think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for the tubular model
num_tubules = 18  # Total number of tubules
ellipse_ratio = 1.4  # Ellipticity factor
radius_value = 0.09  # Radius of the tubules

def build_tubule_model(tubule_count, ellipticity, radius):
    # This function builds a cube and subtracts tubules from it.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(tubule_count)]
    
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        
        bool_modifier = cube.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Build the tubular model
build_tubule_model(num_tubules, ellipse_ratio, radius_value)
