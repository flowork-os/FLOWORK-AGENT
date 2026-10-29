# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code__make_a_model_of_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code, make a model of a tubular bioinspired structure.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the tubular formation
number_of_tubules = 16  # Total count of tubules
stretch_factor = 1.5  # Ellipticity factor for tubules
base_radius = 0.07  # Radius of the tubules

def build_tubule_structure(tubule_count, ellipticity=1.0, radius=0.1):
    # Constructs a cubic structure with a grid of tubular forms.
    # Steps:
    # 1. Create a cube.
    # 2. Arrange tubules in a grid.
    # 3. Apply Boolean modifiers for subtraction.
    
    # Add a cube as the base object
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    
    # Determine grid layout for tubules
    grid_dimension = math.ceil(math.sqrt(tubule_count))
    spacing_between_tubules = 2 / grid_dimension
    initial_offset = -1 + spacing_between_tubules / 2
    
    # Calculate positions for each tubule
    tubule_positions = [(initial_offset + (i % grid_dimension) * spacing_between_tubules, 
                         initial_offset + (i // grid_dimension) * spacing_between_tubules) 
                        for i in range(tubule_count)]
    
    # Subtract each tubule from the cube
    for pos_x, pos_y in tubule_positions:
        # Create a cylinder at the determined position
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(pos_x, pos_y, 0))
        current_tubule = bpy.context.object
        current_tubule.scale[0] *= ellipticity  # Apply the ellipticity factor

        # Set up Boolean modifier to cut the tubule from the cube
        bool_modifier = main_cube.modifiers.new(name=f"Boolean_{pos_x}_{pos_y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = current_tubule

        # Apply the Boolean operation
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        
        # Remove the tubule object
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Create the tubular structure
build_tubule_structure(number_of_tubules, stretch_factor, base_radius)
