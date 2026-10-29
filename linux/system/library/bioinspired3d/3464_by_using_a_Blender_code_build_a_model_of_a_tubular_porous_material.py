# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code_build_a_model_of_a_tubular_porous_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code build a model of a tubular porous material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the structure
num_tubules = 12  # Total number of tubules
stretch_factor = 1.3  # Ellipticity of tubules
base_radius = 0.06  # Radius of tubules

def generate_tubule_structure(num_tubules, stretch_factor=1.0, base_radius=0.1):
    # Create a cube and subtract tubules from it
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    distance = 2 / grid_size
    offset = -1 + distance / 2
    positions = [(offset + (i % grid_size) * distance, offset + (i // grid_size) * distance) for i in range(num_tubules)]
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=base_radius, depth=3, location=(x, y, 0))
        tubule = bpy.context.object
        tubule.scale[0] *= stretch_factor
        modifier = cube.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = tubule
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(tubule, do_unlink=True)

generate_tubule_structure(num_tubules, stretch_factor, base_radius)
