# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_blender_code__generate_a_cube_of_tubular_bioinspired_material_Think_step" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a blender code, generate a cube of tubular bioinspired material Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular structure
num_tubules = 15  # Total count of tubules
stretch_factor = 1.5  # Ellipticity factor for tubules
base_radius = 0.07  # Base radius of the tubules

def generate_tubule_structure(tubule_count, ellipticity=1.0, radius=0.1):
    # Create a base cube and subtract tubules from it.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dimension
    offset = -1 + spacing / 2
    
    positions = [(offset + (i % grid_dimension) * spacing, offset + (i // grid_dimension) * spacing) for i in range(tubule_count)]
    
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        
        bool_modifier = main_cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure with specified parameters
generate_tubule_structure(num_tubules, stretch_factor, base_radius)
