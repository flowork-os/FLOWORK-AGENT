# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_tubular_porous_structure_using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a tubular porous structure using blender python code

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
num_tubules = 18
ellipticity = 1.4
radius = 0.09

def create_tubule_structure(tubule_count, ellipticity_factor, radius_value):
    # Create a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2

    # Calculate positions for tubules
    positions = [(start_offset + (i % grid_size) * spacing,
                  start_offset + (i // grid_size) * spacing)
                 for i in range(tubule_count)]

    # Create and subtract tubules
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius_value, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity_factor

        # Create a Boolean modifier to subtract the tubule
        bool_modifier = base_cube.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule

        # Apply the modifier
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the tubular structure
create_tubule_structure(num_tubules, ellipticity, radius)
