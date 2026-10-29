# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_script_that_creates_a_cube_of_tubular_material_think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender script that creates a cube of tubular material think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 16  # Number of tubules in the structure

def generate_tubules():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(num_tubules))
    separation = 2 / grid_dimension
    initial_offset = -1 + separation / 2
    
    coordinates = [(initial_offset + (i % grid_dimension) * separation,
                    initial_offset + (i // grid_dimension) * separation)
                   for i in range(num_tubules)]
    
    for x_pos, y_pos in coordinates:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
        tubule_cylinder = bpy.context.object

        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{x_pos}_{y_pos}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_cylinder

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

        bpy.data.objects.remove(tubule_cylinder, do_unlink=True)

generate_tubules()
