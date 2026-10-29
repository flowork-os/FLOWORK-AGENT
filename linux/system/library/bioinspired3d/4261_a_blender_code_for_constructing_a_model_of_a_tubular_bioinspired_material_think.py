# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_constructing_a_model_of_a_tubular_bioinspired_material_think" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for constructing a model of a tubular bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
number_of_tubules = 9
ellipse_scale_factor = 2.0
radius_value = 0.1

def build_tubule_cube(num_tubules, scale=1.0, radius=0.1):
    # Create a cube and subtract tubules to form structure
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(num_tubules))
    spacing_between = 2 / grid_dimension
    offset_start = -1 + spacing_between / 2
    
    coordinates = [(offset_start + (i % grid_dimension) * spacing_between, offset_start + (i // grid_dimension) * spacing_between) for i in range(num_tubules)]
    
    for coord_x, coord_y in coordinates:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(coord_x, coord_y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= scale
        
        boolean_modifier = cube_object.modifiers.new(name=f"Subtract_{coord_x}_{coord_y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the building of the structure
build_tubule_cube(number_of_tubules, ellipse_scale_factor, radius_value)
