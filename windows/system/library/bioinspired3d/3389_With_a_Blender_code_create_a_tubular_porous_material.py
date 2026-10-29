# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code_create_a_tubular_porous_material" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code create a tubular porous material

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define parameters for the tubule array
count_tubules = 20
stretch_amount = 1.8
radius_tubule = 0.1

def generate_tubule_grid(count, stretch, radius):
    # Generate a grid of tubules within a cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    offset = -1 + spacing / 2

    # Create positions for tubules
    positions = [(offset + (i % grid_size) * spacing, offset + (i // grid_size) * spacing) for i in range(count)]

    for pos in positions:
        create_tubule(base_cube, pos[0], pos[1], radius, stretch)


def create_tubule(cube, x, y, radius, stretch):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=3, location=(x, y, 0))
    tubule = bpy.context.object
    tubule.scale[0] *= stretch
    mod = cube.modifiers.new(name=f'Boolean_{x}_{y}', type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = tubule
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(tubule, do_unlink=True)

# Execute the grid generation
generate_tubule_grid(count_tubules, stretch_amount, radius_tubule)
