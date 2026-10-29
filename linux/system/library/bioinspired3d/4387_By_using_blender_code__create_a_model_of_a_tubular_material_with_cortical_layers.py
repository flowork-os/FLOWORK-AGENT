# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code__create_a_model_of_a_tubular_material_with_cortical_layers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code, create a model of a tubular material with cortical layers. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Configuration for the tubular model
count_of_tubules = 20  # Number of tubules in the model
layer_thickness_value = 0.06  # Thickness of the layer around each tubule

def create_tubular_model():
    # Add a cube as the base shape
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_shape = bpy.context.object

    # Calculate grid dimensions
    grid_dimension = math.ceil(math.sqrt(count_of_tubules))
    distance_between_tubules = 2 / grid_dimension
    initial_offset = -1 + distance_between_tubules / 2

    # Generate tubule positions
    tubule_coordinates = [(initial_offset + (i % grid_dimension) * distance_between_tubules,
                          initial_offset + (i // grid_dimension) * distance_between_tubules)
                         for i in range(count_of_tubules)]

    created_tubules = []

    for coord_x, coord_y in tubule_coordinates:
        # Create inner cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(coord_x, coord_y, 0))
        inner_cylinder = bpy.context.object

        # Create outer cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness_value, depth=2, location=(coord_x, coord_y, 0))
        outer_cylinder = bpy.context.object

        # Boolean modifier to subtract inner cylinder from the cube
        boolean_modifier = base_shape.modifiers.new(name=f"Boolean_{coord_x}_{coord_y}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = inner_cylinder
        bpy.context.view_layer.objects.active = base_shape
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)

        # Boolean modifier to create the hollow around the inner cylinder
        layer_modifier = inner_cylinder.modifiers.new(name=f"Layer_{coord_x}_{coord_y}", type='BOOLEAN')
        layer_modifier.operation = 'DIFFERENCE'
        layer_modifier.object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=layer_modifier.name)

        # Remove the outer cylinder
        bpy.data.objects.remove(outer_cylinder, do_unlink=True)

        created_tubules.append(inner_cylinder)

    # Merge all inner cylinders into one object
    if created_tubules:
        bpy.ops.object.select_all(action='DESELECT')
        for tubule in created_tubules:
            tubule.select_set(True)
        bpy.context.view_layer.objects.active = created_tubules[0]
        bpy.ops.object.join()
        final_tubular_model = bpy.context.object
        final_tubular_model.name = "Final_Tubular_Model"

# Call the function to create the model
create_tubular_model()
