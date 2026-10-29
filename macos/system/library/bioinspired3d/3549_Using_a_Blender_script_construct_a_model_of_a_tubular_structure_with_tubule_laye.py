# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_script_construct_a_model_of_a_tubular_structure_with_tubule_laye" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender script construct a model of a tubular structure with tubule layers

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for creating the tubular structure
num_tubules = 18  # Number of tubules
layer_thickness = 0.07  # Layer thickness

def setup_tubules():
    # Function to create a cube with a grid of tubules surrounded by layers.
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube_base = bpy.context.object
    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start = -1 + spacing / 2
    positions = [(start + (i % grid_size) * spacing, start + (i // grid_size) * spacing) for i in range(num_tubules)]
    layer_objects = []
    for pos in positions:
        x, y = pos
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
        inner_cylinder = bpy.context.object
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
        outer_cylinder = bpy.context.object
        cube_base.modifiers.new(name=f"Bool_{x}_{y}", type='BOOLEAN')
        cube_base.modifiers[-1].operation = 'DIFFERENCE'
        cube_base.modifiers[-1].object = inner_cylinder
        bpy.context.view_layer.objects.active = cube_base
        bpy.ops.object.modifier_apply(modifier=cube_base.modifiers[-1].name)
        inner_cylinder.modifiers.new(name=f"Layer_Bool_{x}_{y}", type='BOOLEAN')
        inner_cylinder.modifiers[-1].operation = 'DIFFERENCE'
        inner_cylinder.modifiers[-1].object = outer_cylinder
        bpy.context.view_layer.objects.active = inner_cylinder
        bpy.ops.object.modifier_apply(modifier=inner_cylinder.modifiers[-1].name)
        bpy.data.objects.remove(outer_cylinder, do_unlink=True)
        layer_objects.append(inner_cylinder)
    if layer_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in layer_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = layer_objects[0]
        bpy.ops.object.join()
        final_tubule_structure = bpy.context.object
        final_tubule_structure.name = "Tubule_Grid_Structure"

# Initiate the setup
setup_tubules()
