# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_that_generates_a_model_of_a_cube_of_tubular_bioinspired_ma" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender that generates a model of a cube of tubular bioinspired material. think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

total_tubules = 18
ellipticity_value = 1.6
radius_value = 0.05

def create_tubule_design(tubule_count, ellipticity, radius):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    main_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2
    for i in range(tubule_count):
        x = offset + (i % grid_size) * spacing
        y = offset + (i // grid_size) * spacing
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        boolean_modifier = main_cube.modifiers.new(name=f"Subtract_{i}", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'
        boolean_modifier.object = tubule
        bpy.context.view_layer.objects.active = main_cube
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

create_tubule_design(total_tubules, ellipticity_value, radius_value)
