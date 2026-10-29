# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_making_a_tubular_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for making a tubular structure

import bpy
import math

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
total_tubules = 20
ellipse_scale = 1.3
tubule_diameter = 0.06

def create_tubule_pattern(tubule_count, scale_factor, diameter):
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing_value = 2 / grid_dim
    offset_value = -1 + spacing_value / 2

    # Determine positions for the tubules
    positions = [(offset_value + (i % grid_dim) * spacing_value,
                  offset_value + (i // grid_dim) * spacing_value)
                 for i in range(tubule_count)]

    # Subtract tubules from cube
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=diameter, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= scale_factor

        bool_modifier = base_cube.modifiers.new(name=f"Subtract_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule

        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Execute the creation of the pattern
create_tubule_pattern(total_tubules, ellipse_scale, tubule_diameter)
