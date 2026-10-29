# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_building_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for building a tubular porous structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular formation
number_of_tubules = 16  # Total tubules in the structure
stretch_factor = 1.5  # Factor to stretch tubules into ellipses
base_radius = 0.07  # Base radius of the tubules

# Function to create the tubule structure

def build_tubule_structure(tubule_count, ellipticity=1.0, tubule_radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dimension = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dimension
    initial_offset = -1 + spacing / 2

    # Calculate positions for tubules
    tubule_positions = [(initial_offset + (i % grid_dimension) * spacing, 
                         initial_offset + (i // grid_dimension) * spacing) 
                        for i in range(tubule_count)]

    for pos_x, pos_y in tubule_positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=tubule_radius, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        bool_modifier = main_cube.modifiers.new(name=f"Bool_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the function to create the structure
build_tubule_structure(number_of_tubules, stretch_factor, base_radius)
