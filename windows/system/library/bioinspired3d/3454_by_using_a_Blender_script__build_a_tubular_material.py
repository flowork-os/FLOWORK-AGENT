# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script__build_a_tubular_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script, build a tubular material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the creation of the tubule structure
total_tubules = 12  # Number of tubules
stretch_factor = 1.8  # Ellipticity of the tubules
base_radius = 0.06  # Radius of the tubules

def generate_tubule_structure(tubule_count, ellipticity=1.0, radius=0.1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(tubule_count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2

    positions = [(start_offset + (i % grid_size) * spacing, 
                  start_offset + (i // grid_size) * spacing) 
                 for i in range(tubule_count)]

    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= ellipticity
        bool_modifier = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

# Create the tubular structure
generate_tubule_structure(total_tubules, stretch_factor, base_radius)
