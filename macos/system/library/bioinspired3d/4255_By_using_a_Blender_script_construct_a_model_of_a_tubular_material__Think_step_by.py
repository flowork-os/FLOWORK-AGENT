# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_construct_a_model_of_a_tubular_material__Think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script construct a model of a tubular material. Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule parameters
count_of_tubules = 12  # Total number of tubules
stretch = 1.3  # Ellipticity factor
base_tubule_radius = 0.06  # Radius of the tubules

def create_tubule_array(count, stretch, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    start_pos = -1 + spacing / 2
    
    positions = [(start_pos + (i % grid_dim) * spacing, start_pos + (i // grid_dim) * spacing) for i in range(count)]
    
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= stretch
        
        bool_modifier = cube.modifiers.new(name=f"Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the array of tubules
create_tubule_array(count_of_tubules, stretch, base_tubule_radius)
