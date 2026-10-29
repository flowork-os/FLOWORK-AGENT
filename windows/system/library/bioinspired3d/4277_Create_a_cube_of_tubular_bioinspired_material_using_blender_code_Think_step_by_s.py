# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_cube_of_tubular_bioinspired_material_using_blender_code_Think_step_by_s" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a cube of tubular bioinspired material using blender code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Total number of tubules
stretch_factor = 1.5  # Factor to stretch tubules into ellipses
base_radius = 0.08  # Base radius of the tubules

def build_tubule_structure(total_tubules, stretch=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2
    
    coordinates = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(total_tubules)]
    
    for coord in coordinates:
        x, y = coord
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule_obj = bpy.context.object
        tubule_obj.scale[0] *= stretch  # Apply stretch factor
        
        bool_modifier = cube_obj.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_obj
        
        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        bpy.data.objects.remove(tubule_obj, do_unlink=True)

build_tubule_structure(num_tubules, stretch_factor, base_radius)
