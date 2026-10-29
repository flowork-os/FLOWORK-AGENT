# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_create_a_tubular_bioinspired_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to create a tubular bioinspired material.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule configuration
total_tubules = 20  # Number of tubules
stretch_ratio = 1.2  # Ellipticity factor
radius_of_tubules = 0.05  # Radius of each tubule

def create_tubule_grid(count, ratio=1.0, radius=0.1):
    # Constructs a cube with a grid of cylindrical tubules.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    dimension = math.ceil(math.sqrt(count))
    distance = 2 / dimension
    offset_start = -1 + distance / 2
    coords = [(offset_start + (i % dimension) * distance, 
                offset_start + (i // dimension) * distance) 
               for i in range(count)]
    for coord_x, coord_y in coords:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(coord_x, coord_y, 0))
        tubule_instance = bpy.context.object
        tubule_instance.scale[0] *= ratio
        boolean_modifier = cube_object.modifiers.new(name=f"Bool_{coord_x}_{coord_y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule_instance
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule_instance, do_unlink=True)

# Execute the creation of the tubule grid
create_tubule_grid(total_tubules, stretch_ratio, radius_of_tubules)
