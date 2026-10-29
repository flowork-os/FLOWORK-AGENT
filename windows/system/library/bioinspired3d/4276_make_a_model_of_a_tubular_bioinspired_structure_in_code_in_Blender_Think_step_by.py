# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_a_tubular_bioinspired_structure_in_code_in_Blender_Think_step_by" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of a tubular bioinspired structure in code in Blender Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular model
number_of_tubules = 18  # Total number of tubules
stretch_ratio = 1.3  # Ellipticity
radius_of_tubules = 0.08  # Radius of tubules

def make_tubular_model(tubule_count, stretch=1.0, radius=0.1):
    # Create a grid of cylindrical tubules within a cube.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_shape = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(tubule_count))
    spacing_distance = 2 / grid_dimension
    initial_offset = -1 + spacing_distance / 2
    positions = [(initial_offset + (i % grid_dimension) * spacing_distance, 
                  initial_offset + (i // grid_dimension) * spacing_distance) 
                 for i in range(tubule_count)]
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= stretch
        bool_mod = cube_shape.modifiers.new(name=f"Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = current_tubule
        bpy.context.view_layer.objects.active = cube_shape
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the tubular model creation
make_tubular_model(number_of_tubules, stretch_ratio, radius_of_tubules)
