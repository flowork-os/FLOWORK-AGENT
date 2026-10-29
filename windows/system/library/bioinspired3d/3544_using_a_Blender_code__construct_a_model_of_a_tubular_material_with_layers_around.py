# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_code__construct_a_model_of_a_tubular_material_with_layers_around" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender code, construct a model of a tubular material with layers around each tubule.

import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Tubule configuration
num_tubules = 12
layer_thickness = 0.03

def create_structure():
    # Create the base cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_cube = bpy.context.object

    grid_size = math.ceil(math.sqrt(num_tubules))
    spacing = 2 / grid_size
    start = -1 + spacing / 2

    for i in range(num_tubules):
        x = start + (i % grid_size) * spacing
        y = start + (i // grid_size) * spacing
        create_tubule(base_cube, x, y)

def create_tubule(cube, x, y):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
    inner = bpy.context.object

    bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
    outer = bpy.context.object

    apply_boolean(cube, inner)
    apply_boolean(inner, outer)
    bpy.data.objects.remove(outer, do_unlink=True)

def apply_boolean(target, obj):
    mod = target.modifiers.new(name='Bool', type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = obj
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)

# Build the tubular structure
create_structure()
