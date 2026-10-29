# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script__generate_a_model_of_a_tubular_bioinspired_structure_Thi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script, generate a model of a tubular bioinspired structure Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular structure
num_tubules = 9  # Total number of tubules
elliptic_factor = 2.0  # Ellipticity of the tubules
radius_of_tubule = 0.09  # Radius of the tubules

def create_structure(num_tubules, elliptic_factor=1.0, radius_of_tubule=0.1):
    # Create a cube and subtract tubules from it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    grid_dim = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2
    for i in range(num_tubules):
        x_pos = start_offset + (i % grid_dim) * spacing
        y_pos = start_offset + (i // grid_dim) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_tubule, depth=3, location=(x_pos, y_pos, 0))
        tubule_object = bpy.context.object
        tubule_object.scale[0] *= elliptic_factor
        bool_modifier = cube_object.modifiers.new(name=f"Subtract_{x_pos}_{y_pos}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_object
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule_object, do_unlink=True)

create_structure(num_tubules, elliptic_factor, radius_of_tubule)
