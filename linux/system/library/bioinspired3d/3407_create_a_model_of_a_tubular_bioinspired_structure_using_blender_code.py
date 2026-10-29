# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_a_tubular_bioinspired_structure_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of a tubular bioinspired structure using blender code

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure settings
count_tubules = 25
ellipse_factor = 1.2
radius_tubule = 0.05

# Function to generate a cube with tubules

def create_tubular_structure(tubule_count, ellipticity, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_dim = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_dim
    start_offset = -1 + spacing / 2
    
    # Generate positions for the tubules
    positions = []
    for i in range(tubule_count):
        x = start_offset + (i % grid_dim) * spacing
        y = start_offset + (i // grid_dim) * spacing
        positions.append((x, y))
    
    # Subtract tubules from the cube
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        
        # Create and apply Boolean modifier
        modifier = main_cube.modifiers.new(name=f"Subtraction_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Run the structure creation
create_tubular_structure(count_tubules, ellipse_factor, radius_tubule)
