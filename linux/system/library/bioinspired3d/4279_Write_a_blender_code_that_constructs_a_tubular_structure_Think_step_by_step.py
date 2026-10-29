# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_that_constructs_a_tubular_structure_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code that constructs a tubular structure Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 20  # Total number of tubules
stretch_ratio = 1.8  # Ellipticity factor
base_tubule_radius = 0.07  # Radius of tubules

def generate_tubule_cube(tubule_count, stretch, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dim
    start_pos = -1 + spacing / 2
    
    positions = [(start_pos + (i % grid_dim) * spacing, start_pos + (i // grid_dim) * spacing) for i in range(tubule_count)]
    
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= stretch  # Apply stretch ratio
        
        mod = cube.modifiers.new(name=f"Subtract_{x}_{y}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=mod.name)
        
        bpy.data.objects.remove(tubule, do_unlink=True)

generate_tubule_cube(num_tubules, stretch_ratio, base_tubule_radius)
