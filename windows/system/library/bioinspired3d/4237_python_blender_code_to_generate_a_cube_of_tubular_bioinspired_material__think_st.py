# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_generate_a_cube_of_tubular_bioinspired_material__think_st" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to generate a cube of tubular bioinspired material. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Total number of tubules
stretch_factor = 1.5  # Ellipticity factor for tubules
base_radius = 0.07  # Radius of each tubule

def build_tubule_grid(tubule_count, ellipticity=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(tubule_count)]
    
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        tubule_instance = bpy.context.object
        tubule_instance.scale[0] *= ellipticity
        
        bool_modifier = cube_object.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_instance
        
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule_instance, do_unlink=True)

build_tubule_grid(num_tubules, stretch_factor, base_radius)
