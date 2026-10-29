# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_blender_code_that_creates_a_model_of_a_cube_of_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create blender code that creates a model of a cube of tubular material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Number of cylinders to create in the structure
cylinder_count = 9

def build_structure_with_cylinders():
    # Constructs a cube and subtracts cylinders to form a pattern
    
    # Add a cube to the scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_object = bpy.context.object
    
    grid_dimension = math.ceil(math.sqrt(cylinder_count))
    interval = 2 / grid_dimension
    initial_position = -1 + interval / 2

    for i in range(cylinder_count):
        x_pos = initial_position + (i % grid_dimension) * interval
        y_pos = initial_position + (i // grid_dimension) * interval
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x_pos, y_pos, 0))
        cylinder_object = bpy.context.object
        
        boolean_modifier = cube_object.modifiers.new(name=f"Subtraction_{i}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = cylinder_object
        
        bpy.context.view_layer.objects.active = cube_object
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(cylinder_object, do_unlink=True)

# Call the function to build the structure
build_structure_with_cylinders()
