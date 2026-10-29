# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_code_that_constructs_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender code that constructs a tubular porous structure

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule count for the structure
tubule_count = 25  # Selected number of tubules

def create_tubular_grid():
    # This function constructs a grid of tubules within a cube.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    grid_dim = math.ceil(math.sqrt(tubule_count))
    tube_spacing = 2 / grid_dim
    offset = -1 + tube_spacing / 2
    
    for i in range(tubule_count):
        x_position = offset + (i % grid_dim) * tube_spacing
        y_position = offset + (i // grid_dim) * tube_spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_position, y_position, 0))
        current_tube = bpy.context.object
        bool_mod = cube_obj.modifiers.new(name=f"Subtraction_{i}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tube
        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(current_tube, do_unlink=True)

create_tubular_grid()
