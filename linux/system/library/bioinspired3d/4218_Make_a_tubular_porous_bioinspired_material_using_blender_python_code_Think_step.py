# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_tubular_porous_bioinspired_material_using_blender_python_code_Think_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a tubular porous bioinspired material using blender python code Think step by step.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular design
num_tubules = 16  # Total number of tubules in the structure
ellipse_factor = 1.5  # Factor to stretch tubules into ellipses
base_radius = 0.08  # Base radius of the tubules

def build_tubule_structure(tubule_count, ellipticity=1.0, radius=0.1):
    # Constructs a cube with a grid of tubules of specified size and shape.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2

    # Calculate positions for tubules within the grid
    positions = [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(tubule_count)]
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        modifier = main_cube.modifiers.new(name=f'Boolean_{x}_{y}', type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
build_tubule_structure(num_tubules, ellipse_factor, base_radius)
