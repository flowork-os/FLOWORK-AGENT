# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_builds_a_tubular_porous_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that builds a tubular porous structure

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Total number of cylinders to create
cylinder_count = 18

def main():
    # Main function to create the structure
    base_cube = add_cube()
    tubule_coords = generate_coordinates(cylinder_count)
    apply_boolean(base_cube, tubule_coords)

def add_cube():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.object

def generate_coordinates(count):
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    start = -1 + spacing / 2
    return [(start + (i % grid_size) * spacing, start + (i // grid_size) * spacing) for i in range(count)]

def apply_boolean(cube, positions):
    for x, y in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3, location=(x, y, 0))
        cylinder = bpy.context.object

        bool_mod = cube.modifiers.new(name=f"Boolean_{x}_{y}", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cylinder

        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(cylinder, do_unlink=True)

# Execute main function
main()
