# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_a_tubular_bioinspired_structure_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of a tubular bioinspired structure using code in Blender

import bpy
import math

# Remove all objects from the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Count of tubular shapes
total_tubules = 20

# Main function to create the geometry

def create_geometry():
    # Start by adding a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_shape = bpy.context.object

    # Calculate grid dimensions
    grid_dim = math.ceil(math.sqrt(total_tubules))
    distance = 2 / grid_dim
    offset = -1 + distance / 2

    # Loop to create tubules
    for index in range(total_tubules):
        x_pos = offset + (index % grid_dim) * distance
        y_pos = offset + (index // grid_dim) * distance
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
        current_tubule = bpy.context.object

        # Apply Boolean modifier to cut out the tubule from the cube
        modifier = base_shape.modifiers.new(name=f"Cut_{index}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = current_tubule

        bpy.context.view_layer.objects.active = base_shape
        bpy.ops.object.modifier_apply(modifier=modifier.name)

        # Clean up by removing the tubule
        bpy.data.objects.remove(current_tubule, do_unlink=True)

# Call the main geometry creation function
create_geometry()
