# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_blender_code_that_constructs_a_model_of_a_tubular_porous_bioinspired_mate" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a blender code that constructs a model of a tubular porous bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular grid
total_tubules = 14
ellipse_ratio = 1.3
cylinder_radius = 0.09

# Function to create the grid of tubules
def generate_tubule_grid(total_tubules, ellipse_ratio, cylinder_radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(total_tubules))
    spacing = 2 / grid_size
    origin_offset = -1 + spacing / 2

    for index in range(total_tubules):
        x_position = origin_offset + (index % grid_size) * spacing
        y_position = origin_offset + (index // grid_size) * spacing
        create_tubule(base_cube, x_position, y_position, cylinder_radius, ellipse_ratio)

def create_tubule(base_cube, x, y, radius, ellipse):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
    tubule_obj = bpy.context.object
    tubule_obj.scale[0] *= ellipse

    boolean_modifier = base_cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
    boolean_modifier.operation = 'DIFFERENCE'
    boolean_modifier.object = tubule_obj

    bpy.context.view_layer.objects.active = base_cube
    bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
    bpy.data.objects.remove(tubule_obj, do_unlink=True)

# Run the function to create the grid
generate_tubule_grid(total_tubules, ellipse_ratio, cylinder_radius)
