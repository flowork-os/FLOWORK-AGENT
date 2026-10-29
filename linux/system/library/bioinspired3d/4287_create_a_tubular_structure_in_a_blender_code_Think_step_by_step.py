# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_tubular_structure_in_a_blender_code_Think_step_by_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a tubular structure in a blender code Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular grid
num_tubules = 16  # Total number of tubules
ellipse_factor = 1.5  # Stretching factor for the tubules
base_radius = 0.07  # Radius of the tubules

# Function to create a grid of tubules within a cube
def build_tubule_structure(count, ellipticity=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    grid_dim = math.ceil(math.sqrt(count))
    spacing = 2 / grid_dim
    offset = -1 + spacing / 2

    # Calculate positions for each tubule
    positions = [(offset + (i % grid_dim) * spacing, offset + (i // grid_dim) * spacing) for i in range(count)]

    for position in positions:
        x, y = position
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule_obj = bpy.context.object
        tubule_obj.scale[0] *= ellipticity

        # Use a Boolean modifier to subtract the tubule from the cube
        boolean_modifier = cube_obj.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule_obj

        # Apply the modifier
        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule_obj, do_unlink=True)

# Execute the function to create the structure
build_tubule_structure(num_tubules, ellipse_factor, base_radius)
