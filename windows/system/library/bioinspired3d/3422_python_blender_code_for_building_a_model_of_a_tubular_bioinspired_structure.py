# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_building_a_model_of_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for building a model of a tubular bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule configuration
total_tubules = 20  # Number of tubules in the structure
ellipse_factor = 1.2  # Stretch factor for tubules
radius_of_tubules = 0.05  # Radius of the tubules


def create_tubule_grid(count, ellipticity, radius):
    # This function constructs a grid of tubules and subtracts them from a cube.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    initial_offset = -1 + spacing / 2
    
    positions = [(initial_offset + (i % grid_size) * spacing, initial_offset + (i // grid_size) * spacing) for i in range(count)]
    
    for pos_x, pos_y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        
        bool_mod = base_cube.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = tubule
        
        bpy.context.view_layer.objects.active = base_cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Generate the grid of tubules
create_tubule_grid(total_tubules, ellipse_factor, radius_of_tubules)
