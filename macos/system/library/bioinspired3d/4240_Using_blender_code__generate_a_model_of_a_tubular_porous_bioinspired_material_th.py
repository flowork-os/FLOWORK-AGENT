# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_code__generate_a_model_of_a_tubular_porous_bioinspired_material_th" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender code, generate a model of a tubular porous bioinspired material think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 12
ellipse_ratio = 1.4
tubule_diameter = 0.06

def generate_tubule_cube(tubule_count, ellipticity, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    
    for i in range(tubule_count):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        
        bool_mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

generate_tubule_cube(num_tubules, ellipse_ratio, tubule_diameter)
