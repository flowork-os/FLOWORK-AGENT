# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_Python_script_that_constructs_a_model_of_a_tubular_bioinspired_str" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender Python script that constructs a model of a tubular bioinspired structure think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubular structure parameters
num_of_tubules = 14
ellipticity_factor = 1.1
radius_tube = 0.08

def calculate_tubule_positions(tubule_count):
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    return [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(tubule_count)]

# Main function to create the tubule structure
def create_tubule_structure():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_obj = bpy.context.object
    positions = calculate_tubule_positions(num_of_tubules)

    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius_tube, depth=3, location=(x, y, 0))
        tubule_obj = bpy.context.object
        tubule_obj.scale[0] *= ellipticity_factor

        # Create and apply Boolean modifier
        bool_modifier = cube_obj.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule_obj

        bpy.context.view_layer.objects.active = cube_obj
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule_obj, do_unlink=True)

# Execute the creation of the structure
create_tubule_structure()
