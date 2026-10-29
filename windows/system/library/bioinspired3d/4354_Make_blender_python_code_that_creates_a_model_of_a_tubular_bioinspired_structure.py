# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_blender_python_code_that_creates_a_model_of_a_tubular_bioinspired_structure" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make blender python code that creates a model of a tubular bioinspired structure with tubule layers Think step by step

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_tubules = 12  # Total tubules
layer_thickness = 0.04  # Thickness of each layer

def setup_scene():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    return bpy.context.object

def generate_positions(count):
    grid_size = math.ceil(math.sqrt(count))
    spacing = 2 / grid_size
    start_offset = -1 + spacing / 2
    return [(start_offset + (i % grid_size) * spacing, start_offset + (i // grid_size) * spacing) for i in range(count)]

def create_tubule(cube, position):
    x, y = position
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(x, y, 0))
    inner_tubule = bpy.context.object
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1 - layer_thickness, depth=2, location=(x, y, 0))
    outer_tubule = bpy.context.object
    apply_boolean(cube, inner_tubule)
    apply_boolean(inner_tubule, outer_tubule)
    bpy.data.objects.remove(outer_tubule, do_unlink=True)
    return inner_tubule

def apply_boolean(target, obj):
    mod = target.modifiers.new(name="Bool_Modifier", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = obj
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)

def merge_objects(objects):
    if objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        merged_object = bpy.context.object
        merged_object.name = "Tubule_Structure"

# Main execution
cube = setup_scene()
positions = generate_positions(num_tubules)
layer_objects = [create_tubule(cube, pos) for pos in positions]
merge_objects(layer_objects)
